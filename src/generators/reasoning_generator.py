"""Reasoning generator for trading decisions."""
import json
import logging
import random
import re
from typing import Dict, Any, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from templates.prompts import get_reasoning_prompt
from src.workers.api_client import OpenRouterClient

logger = logging.getLogger(__name__)


class ReasoningGenerator:
    """Generate reasoning traces for scenarios."""
    
    def __init__(self, client: OpenRouterClient, models: List[str]):
        self.client = client
        self.models = models
    
    async def generate(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Generate reasoning trace for a scenario."""
        # Select model
        model = random.choice(self.models)
        
        # Build prompt
        prompt = get_reasoning_prompt(scenario)
        messages = [
            {"role": "system", "content": "You are Dexter, a crypto trading bot assistant. Provide structured trading reasoning with decisions."},
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = await self.client.generate(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )
            
            text = await self.client.extract_text(response)
            
            # Extract reasoning and decision
            reasoning = self._extract_reasoning(text)
            decision = self._extract_decision(text)
            
            return {
                "reasoning": reasoning,
                "decision": decision,
                "full_response": text,
                "_metadata": {
                    "model": model,
                },
            }
        
        except Exception as e:
            logger.error(f"Failed to generate reasoning: {e}")
            raise
    
    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning section from response."""
        match = re.search(r'<reasoning>([\s\S]*?)</reasoning>', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: return first paragraph if no tags
        lines = text.split('\n')
        reasoning_lines = []
        for line in lines:
            if '<decision>' in line.lower():
                break
            reasoning_lines.append(line)
        
        return '\n'.join(reasoning_lines).strip()
    
    def _extract_decision(self, text: str) -> Dict[str, Any]:
        """Extract decision JSON from response."""
        match = re.search(r'<decision>([\s\S]*?)</decision>', text, re.IGNORECASE)
        if match:
            decision_text = match.group(1).strip()
            try:
                return json.loads(decision_text)
            except json.JSONDecodeError:
                # Try to extract JSON from the text
                json_match = re.search(r'\{[\s\S]*\}', decision_text)
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
        
        # Fallback: create basic decision structure
        return {
            "action": "analyze",
            "parameters": {},
            "confidence": 0.5,
            "reasoning_summary": "Unable to parse structured decision",
        }

