"""Configuration and API management for training data generation."""
import os
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration."""
    openrouter_api_key: str
    models: List[str]
    scenario_models: List[str]
    reasoning_models: List[str]
    min_workers: int = 4
    max_workers: int = 16  # Reduced from 32 to prevent overload
    batch_size: int = 1000
    validation_retries: int = 3
    rate_limit_check_interval: int = 5
    db_path: str = "data/training_data.db"
    output_dir: str = "output"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        models_str = os.getenv("MODELS", "")
        if not models_str:
            raise ValueError("MODELS environment variable is required (comma-separated)")
        
        models = [m.strip() for m in models_str.split(",") if m.strip()]
        
        # Split models: first half for scenarios, second half for reasoning
        mid = len(models) // 2
        scenario_models = models[:mid] if mid > 0 else models
        reasoning_models = models[mid:] if mid > 0 else models
        
        return cls(
            openrouter_api_key=api_key,
            models=models,
            scenario_models=scenario_models,
            reasoning_models=reasoning_models,
            min_workers=int(os.getenv("MIN_WORKERS", "4")),
            max_workers=int(os.getenv("MAX_WORKERS", "32")),
            batch_size=int(os.getenv("BATCH_SIZE", "1000")),
            validation_retries=int(os.getenv("VALIDATION_RETRIES", "3")),
            rate_limit_check_interval=int(os.getenv("RATE_LIMIT_CHECK_INTERVAL", "5")),
            db_path=os.getenv("DB_PATH", "data/training_data.db"),
            output_dir=os.getenv("OUTPUT_DIR", "output"),
        )

