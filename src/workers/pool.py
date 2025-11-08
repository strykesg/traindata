"""Auto-scaling worker pool for parallel processing."""
import asyncio
import logging
from typing import List, Callable, Any, Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.workers.api_client import OpenRouterClient
from src.config import Config

logger = logging.getLogger(__name__)


@dataclass
class WorkerMetrics:
    """Metrics for worker pool."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    rate_limit_errors: int = 0
    last_rate_limit: Optional[datetime] = None
    current_workers: int = 0


class WorkerPool:
    """Auto-scaling worker pool."""
    
    def __init__(self, config: Config, client: OpenRouterClient):
        self.config = config
        self.client = client
        self.metrics = WorkerMetrics()
        self.workers: List[asyncio.Task] = []
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.result_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.scale_lock = asyncio.Lock()
        self.current_worker_count = config.min_workers
    
    async def start(self):
        """Start the worker pool."""
        self.running = True
        await self._scale_workers(self.config.min_workers)
        
        # Start scaling monitor
        asyncio.create_task(self._monitor_and_scale())
    
    async def stop(self):
        """Stop all workers gracefully."""
        self.running = False
        
        # Wait for queue to drain
        await self.task_queue.join()
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
    
    async def submit(self, task: Any):
        """Submit a task to the queue."""
        await self.task_queue.put(task)
    
    async def get_result(self) -> Any:
        """Get a result from the result queue."""
        return await self.result_queue.get()
    
    async def _worker(self, worker_id: int, process_fn: Callable):
        """Worker coroutine."""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get task with timeout
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                try:
                    result = await process_fn(task, self.client)
                    await self.result_queue.put(("success", result))
                    self.metrics.completed_tasks += 1
                except Exception as e:
                    error_type = type(e).__name__
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        self.metrics.rate_limit_errors += 1
                        self.metrics.last_rate_limit = datetime.now()
                        await self.result_queue.put(("rate_limit", e))
                    else:
                        await self.result_queue.put(("error", e))
                    self.metrics.failed_tasks += 1
                    logger.error(f"Worker {worker_id} error: {e}")
                finally:
                    self.task_queue.task_done()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} unexpected error: {e}")
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _scale_workers(self, target_count: int):
        """Scale workers to target count."""
        async with self.scale_lock:
            target_count = max(self.config.min_workers, min(target_count, self.config.max_workers))
            
            current_count = len(self.workers)
            
            if target_count > current_count:
                # Scale up
                for i in range(current_count, target_count):
                    worker_id = i + 1
                    # Workers will be started with process_fn passed later
                    logger.info(f"Scaling up: adding worker {worker_id}")
            
            elif target_count < current_count:
                # Scale down (let workers finish naturally)
                to_remove = current_count - target_count
                for i in range(to_remove):
                    if self.workers:
                        worker = self.workers.pop()
                        worker.cancel()
                        logger.info(f"Scaling down: removing worker")
            
            self.current_worker_count = target_count
            self.metrics.current_workers = target_count
    
    async def _monitor_and_scale(self):
        """Monitor metrics and scale workers accordingly."""
        while self.running:
            await asyncio.sleep(self.config.rate_limit_check_interval)
            
            # Check rate limit status
            if self.metrics.last_rate_limit:
                time_since_limit = (datetime.now() - self.metrics.last_rate_limit).total_seconds()
                if time_since_limit < 60:  # Recent rate limit
                    # Scale down
                    target = max(self.config.min_workers, self.current_worker_count // 2)
                    await self._scale_workers(target)
                    continue
            
            # Check queue size
            queue_size = self.task_queue.qsize()
            
            # Scale based on queue size
            if queue_size > 100 and self.current_worker_count < self.config.max_workers:
                # Scale up
                target = min(self.config.max_workers, self.current_worker_count * 2)
                await self._scale_workers(target)
            elif queue_size < 10 and self.current_worker_count > self.config.min_workers:
                # Scale down
                target = max(self.config.min_workers, self.current_worker_count // 2)
                await self._scale_workers(target)
    
    async def start_workers_with_fn(self, process_fn: Callable):
        """Start workers with a specific processing function."""
        for i in range(self.current_worker_count):
            worker = asyncio.create_task(self._worker(i + 1, process_fn))
            self.workers.append(worker)

