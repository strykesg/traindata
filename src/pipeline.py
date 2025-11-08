"""Main pipeline orchestration."""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from src.config import Config
from src.workers.api_client import OpenRouterClient
from src.workers.pool import WorkerPool
from src.generators.scenario_generator import ScenarioGenerator
from src.generators.reasoning_generator import ReasoningGenerator
from src.validation.validator import ValidationPipeline
from src.storage.db import TrainingDataDB

logger = logging.getLogger(__name__)


class TrainingDataPipeline:
    """Main pipeline for generating training data."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[OpenRouterClient] = None
        self.scenario_pool: Optional[WorkerPool] = None
        self.reasoning_pool: Optional[WorkerPool] = None
        self.scenario_generator: Optional[ScenarioGenerator] = None
        self.reasoning_generator: Optional[ReasoningGenerator] = None
        self.validator = ValidationPipeline()
        self.db = TrainingDataDB(config.db_path)
        self.scenario_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.metrics = {
            "scenarios_generated": 0,
            "scenarios_valid": 0,
            "reasoning_generated": 0,
            "reasoning_valid": 0,
            "complete_examples": 0,
            "errors": 0,
        }
    
    async def initialize(self):
        """Initialize pipeline components."""
        self.client = OpenRouterClient(self.config.openrouter_api_key)
        await self.client.__aenter__()
        
        # Create scenario generator
        self.scenario_generator = ScenarioGenerator(
            self.client,
            self.config.scenario_models
        )
        
        # Create reasoning generator
        self.reasoning_generator = ReasoningGenerator(
            self.client,
            self.config.reasoning_models
        )
        
        # Create worker pools
        self.scenario_pool = WorkerPool(self.config, self.client)
        self.reasoning_pool = WorkerPool(self.config, self.client)
        
        await self.scenario_pool.start()
        await self.reasoning_pool.start()
        
        # Start workers with processing functions
        await self.scenario_pool.start_workers_with_fn(self._process_scenario_task)
        await self.reasoning_pool.start_workers_with_fn(self._process_reasoning_task)
        
        # Start coordinator
        asyncio.create_task(self._coordinate_scenarios_to_reasoning())
    
    async def cleanup(self):
        """Cleanup resources."""
        self.running = False
        
        if self.scenario_pool:
            await self.scenario_pool.stop()
        
        if self.reasoning_pool:
            await self.reasoning_pool.stop()
        
        # Flush database
        await self.db.flush()
        
        if self.client:
            await self.client.__aexit__(None, None, None)
    
    async def _process_scenario_task(self, task: Any, client: OpenRouterClient) -> Dict[str, Any]:
        """Process scenario generation task."""
        scenario = await self.scenario_generator.generate()
        scenario["_metadata"]["generated_at"] = datetime.now().isoformat()
        scenario["_metadata"]["scenario_id"] = str(uuid.uuid4())
        return scenario
    
    async def _process_reasoning_task(self, task: Dict[str, Any], client: OpenRouterClient) -> Dict[str, Any]:
        """Process reasoning generation task."""
        scenario = task
        reasoning = await self.reasoning_generator.generate(scenario)
        return {
            "scenario": scenario,
            "reasoning": reasoning,
        }
    
    async def _coordinate_scenarios_to_reasoning(self):
        """Coordinate validated scenarios to reasoning generation."""
        while self.running:
            try:
                # Get result from scenario pool
                result_type, result = await asyncio.wait_for(
                    self.scenario_pool.get_result(),
                    timeout=1.0
                )
                
                if result_type == "success":
                    scenario = result
                    
                    # Validate scenario
                    valid, error = self.validator.validate_scenario(scenario)
                    
                    if valid:
                        self.metrics["scenarios_valid"] += 1
                        # Submit to reasoning pool
                        await self.reasoning_pool.submit(scenario)
                    else:
                        logger.warning(f"Invalid scenario: {error}")
                        # Store as invalid
                        await self.db.insert(
                            scenario,
                            {},
                            validation_status="INVALID",
                            validation_error=error,
                            scenario_id=scenario.get("_metadata", {}).get("scenario_id")
                        )
                
                elif result_type == "rate_limit":
                    logger.warning("Rate limit in scenario generation")
                    await asyncio.sleep(5)
                
                elif result_type == "error":
                    logger.error(f"Scenario generation error: {result}")
                    self.metrics["errors"] += 1
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in coordinator: {e}")
                self.metrics["errors"] += 1
    
    async def _process_reasoning_results(self):
        """Process reasoning generation results."""
        while self.running:
            try:
                result_type, result = await asyncio.wait_for(
                    self.reasoning_pool.get_result(),
                    timeout=1.0
                )
                
                if result_type == "success":
                    data = result
                    scenario = data["scenario"]
                    reasoning = data["reasoning"]
                    
                    # Validate complete example
                    valid, error = self.validator.validate_complete_example(scenario, reasoning)
                    
                    scenario_id = scenario.get("_metadata", {}).get("scenario_id", str(uuid.uuid4()))
                    
                    if valid:
                        self.metrics["complete_examples"] += 1
                        await self.db.insert(
                            scenario,
                            reasoning,
                            validation_status="VALID",
                            scenario_id=scenario_id
                        )
                    else:
                        logger.warning(f"Invalid reasoning: {error}")
                        await self.db.insert(
                            scenario,
                            reasoning,
                            validation_status="INVALID",
                            validation_error=error,
                            scenario_id=scenario_id
                        )
                
                elif result_type == "rate_limit":
                    logger.warning("Rate limit in reasoning generation")
                    await asyncio.sleep(5)
                
                elif result_type == "error":
                    logger.error(f"Reasoning generation error: {result}")
                    self.metrics["errors"] += 1
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing reasoning: {e}")
                self.metrics["errors"] += 1
    
    async def generate(self, target_count: int):
        """Generate training examples."""
        self.running = True
        
        # Start reasoning result processor
        asyncio.create_task(self._process_reasoning_results())
        
        # Submit initial scenario tasks
        initial_tasks = min(target_count, self.config.max_workers * 10)
        for _ in range(initial_tasks):
            await self.scenario_pool.submit(None)
            self.metrics["scenarios_generated"] += 1
        
        # Continue submitting tasks as they complete
        while self.running:
            stats = self.db.get_stats()
            valid_count = stats["valid"]
            
            if valid_count >= target_count:
                logger.info(f"Reached target count: {valid_count}")
                break
            
            # Submit more tasks if queue is low
            queue_size = self.scenario_pool.task_queue.qsize()
            if queue_size < 50:
                for _ in range(min(20, target_count - valid_count)):
                    await self.scenario_pool.submit(None)
                    self.metrics["scenarios_generated"] += 1
            
            # Log progress
            if self.metrics["scenarios_generated"] % 100 == 0:
                logger.info(f"Progress: {valid_count}/{target_count} valid examples")
            
            await asyncio.sleep(1)
        
        # Wait for queues to drain
        await asyncio.sleep(5)
        await self.db.flush()
        
        final_stats = self.db.get_stats()
        logger.info(f"Generation complete. Final stats: {final_stats}")
        logger.info(f"Pipeline metrics: {self.metrics}")

