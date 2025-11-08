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
            {"role": "system", "content": "You are Dexter, an aggressive crypto trading bot. You MUST format your response with <reasoning> and <decision> XML tags. Be a degen trader - use leverage, take calculated risks, prioritize high returns."},
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = await self.client.generate(
                model=model,
                messages=messages,
                temperature=0.8,  # Slightly higher for more creative aggressive reasoning
                max_tokens=2500,  # More tokens for detailed reasoning
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
        # Try exact match first
        match = re.search(r'<reasoning>([\s\S]*?)</reasoning>', text, re.IGNORECASE)
        if match:
            reasoning = match.group(1).strip()
            if len(reasoning) >= 50:  # Minimum length check
                return reasoning
        
        # Try without closing tag
        match = re.search(r'<reasoning>([\s\S]*)', text, re.IGNORECASE)
        if match:
            reasoning = match.group(1).strip()
            # Remove decision section if present
            reasoning = re.sub(r'<decision>[\s\S]*', '', reasoning, flags=re.IGNORECASE).strip()
            if len(reasoning) >= 50:
                return reasoning
        
        # Fallback: extract everything before decision tag
        decision_pos = text.lower().find('<decision>')
        if decision_pos > 0:
            reasoning = text[:decision_pos].strip()
            # Remove any leading markdown or formatting
            reasoning = re.sub(r'^#+\s*', '', reasoning, flags=re.MULTILINE)
            reasoning = re.sub(r'^\*\*.*?\*\*', '', reasoning, flags=re.MULTILINE)
            if len(reasoning) >= 50:
                return reasoning
        
        # Last resort: use first 500 chars
        reasoning = text[:500].strip()
        if len(reasoning) < 50:
            raise ValueError(f"Reasoning too short: {len(reasoning)} chars")
        return reasoning
    
    def _extract_decision(self, text: str) -> Dict[str, Any]:
        """Extract decision JSON from response."""
        # Try exact match first
        match = re.search(r'<decision>([\s\S]*?)</decision>', text, re.IGNORECASE)
        if match:
            decision_text = match.group(1).strip()
            # Try parsing directly
            try:
                return json.loads(decision_text)
            except json.JSONDecodeError:
                pass
            
            # Try to find JSON object in the text
            json_match = re.search(r'\{[\s\S]*\}', decision_text)
            if json_match:
                json_str = json_match.group(0)
                # Find matching braces
                brace_count = 0
                brace_end = -1
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            brace_end = i + 1
                            break
                
                if brace_end > 0:
                    try:
                        return json.loads(json_str[:brace_end])
                    except json.JSONDecodeError:
                        pass
        
        # Try without closing tag
        match = re.search(r'<decision>([\s\S]*)', text, re.IGNORECASE)
        if match:
            decision_text = match.group(1).strip()
            json_match = re.search(r'\{[\s\S]*\}', decision_text)
            if json_match:
                json_str = json_match.group(0)
                brace_count = 0
                brace_end = -1
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            brace_end = i + 1
                            break
                
                if brace_end > 0:
                    try:
                        return json.loads(json_str[:brace_end])
                    except json.JSONDecodeError:
                        pass
        
        # Fallback: try to find any JSON in the text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            json_str = json_match.group(0)
            brace_count = 0
            brace_end = -1
            for i, char in enumerate(json_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i + 1
                        break
            
            if brace_end > 0:
                try:
                    parsed = json.loads(json_str[:brace_end])
                    # Check if it looks like a decision structure
                    if "action" in parsed or "parameters" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    pass
        
        raise ValueError("Could not extract valid decision JSON from response")

