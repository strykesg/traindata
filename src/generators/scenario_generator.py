"""Scenario generator for synthetic trading scenarios."""
import json
import logging
import random
from typing import Dict, Any, List
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from templates.prompts import SCENARIO_TYPES, get_scenario_prompt
from src.workers.api_client import OpenRouterClient

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """Generate synthetic trading scenarios."""
    
    def __init__(self, client: OpenRouterClient, models: List[str]):
        self.client = client
        self.models = models
        self.scenario_types = SCENARIO_TYPES
    
    async def generate(self) -> Dict[str, Any]:
        """Generate a single scenario."""
        # Select random scenario type
        scenario_type = random.choice(self.scenario_types)
        
        # Select model (round-robin or random)
        model = random.choice(self.models)
        
        # Build prompt
        prompt = get_scenario_prompt(scenario_type)
        messages = [
            {"role": "system", "content": "You are an expert at creating realistic crypto trading scenarios for AI training."},
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = await self.client.generate(
                model=model,
                messages=messages,
                temperature=0.8,
                max_tokens=2000,
            )
            
            text = await self.client.extract_text(response)
            
            # Try to extract JSON from response
            scenario = self._extract_json(text)
            
            # Add metadata
            scenario["_metadata"] = {
                "generated_at": None,  # Will be set by pipeline
                "model": model,
                "scenario_type": scenario_type["name"],
            }
            
            return scenario
        
        except Exception as e:
            logger.error(f"Failed to generate scenario: {e}")
            raise
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        # Try to find JSON block
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Try parsing entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"Could not extract valid JSON from response: {text[:200]}")

