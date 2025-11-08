"""Export training data to LLaMA chat template format."""
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any

from src.storage.db import TrainingDataDB

logger = logging.getLogger(__name__)


class TrainingDataExporter:
    """Export training data to fine-tuning format."""
    
    def __init__(self, db: TrainingDataDB, output_dir: str):
        self.db = db
        # Resolve to absolute path (relative to app root)
        if Path(output_dir).is_absolute():
            self.output_dir = Path(output_dir)
        else:
            # Resolve relative to app root (where main.py is)
            # Assuming export.py is in src/, go up to app root
            app_root = Path(__file__).parent.parent.parent
            self.output_dir = (app_root / output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Export directory: {self.output_dir}")
    
    def export_to_llama_format(
        self,
        train_split: float = 0.8,
        val_split: float = 0.1,
        test_split: float = 0.1
    ):
        """Export to LLaMA chat template format."""
        # Validate splits
        assert abs(train_split + val_split + test_split - 1.0) < 0.01, "Splits must sum to 1.0"
        
        # Get all valid examples
        examples = self.db.get_valid_examples()
        
        if not examples:
            logger.warning("No valid examples to export")
            return
        
        # Shuffle
        random.shuffle(examples)
        
        # Split
        total = len(examples)
        train_end = int(total * train_split)
        val_end = train_end + int(total * val_split)
        
        train_examples = examples[:train_end]
        val_examples = examples[train_end:val_end]
        test_examples = examples[val_end:]
        
        logger.info(f"Splitting {total} examples: {len(train_examples)} train, {len(val_examples)} val, {len(test_examples)} test")
        
        # Export each split
        self._export_split(train_examples, "train.jsonl")
        self._export_split(val_examples, "val.jsonl")
        self._export_split(test_examples, "test.jsonl")
        
        logger.info(f"Export complete. Files written to {self.output_dir}")
    
    def _export_split(self, examples: List[Dict[str, Any]], filename: str):
        """Export a split to JSONL file."""
        filepath = self.output_dir / filename
        
        with open(filepath, "w") as f:
            for example in examples:
                scenario = example["scenario"]
                reasoning = example["reasoning"]
                
                # Format as LLaMA chat template
                llama_example = self._format_llama_example(scenario, reasoning)
                f.write(json.dumps(llama_example) + "\n")
        
        logger.info(f"Exported {len(examples)} examples to {filepath}")
    
    def _format_llama_example(
        self,
        scenario: Dict[str, Any],
        reasoning: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format example as LLaMA chat template."""
        # Build market context string
        market_context = scenario.get("market_context", {})
        account_state = scenario.get("account_state", {})
        decision_prompt = scenario.get("decision_prompt", "")
        
        context_str = f"""Market context:
{json.dumps(market_context, indent=2)}

Account state:
{json.dumps(account_state, indent=2)}

What should we do?
{decision_prompt}"""
        
        # Build assistant response
        reasoning_text = reasoning.get("reasoning", "")
        decision = reasoning.get("decision", {})
        
        assistant_content = f"""<reasoning>
{reasoning_text}
</reasoning>

<decision>
{json.dumps(decision, indent=2)}
</decision>"""
        
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "You are Dexter, a crypto trading bot assistant. Provide structured trading reasoning with decisions."
                },
                {
                    "role": "user",
                    "content": context_str
                },
                {
                    "role": "assistant",
                    "content": assistant_content
                }
            ]
        }

