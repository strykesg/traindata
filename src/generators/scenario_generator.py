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
            {"role": "system", "content": "You are an expert at creating realistic crypto trading scenarios. You MUST output ONLY valid JSON with no markdown formatting, no explanations, and no text outside the JSON object."},
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = await self.client.generate(
                model=model,
                messages=messages,
                temperature=0.7,  # Lower temperature for more consistent JSON
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
        """Extract JSON from text response with multiple strategies."""
        # Strategy 1: Look for JSON code blocks
        json_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text, re.IGNORECASE)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Find JSON object boundaries more carefully
        # Look for opening brace, then find matching closing brace
        brace_start = text.find('{')
        if brace_start != -1:
            brace_count = 0
            brace_end = -1
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i + 1
                        break
            
            if brace_end > brace_start:
                json_str = text[brace_start:brace_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        # Strategy 3: Try parsing entire text
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Try to extract and fix common issues
        # Remove markdown formatting
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)  # Remove italic
        cleaned = re.sub(r'^[-*]\s+', '', cleaned, flags=re.MULTILINE)  # Remove list markers
        
        # Try to find JSON again in cleaned text
        brace_start = cleaned.find('{')
        if brace_start != -1:
            brace_count = 0
            brace_end = -1
            for i in range(brace_start, len(cleaned)):
                if cleaned[i] == '{':
                    brace_count += 1
                elif cleaned[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i + 1
                        break
            
            if brace_end > brace_start:
                json_str = cleaned[brace_start:brace_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        raise ValueError(f"Could not extract valid JSON from response: {text[:300]}")

