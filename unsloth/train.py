"""
Fine-tune Qwen3-1.7B using Unsloth on vast.ai GTX 5090.
Uses WandB for logging and HuggingFace for model management.
"""
# CRITICAL: Patch torch.int1 FIRST, before ANY other imports
# torchao accesses torch.int1 at import time in a dictionary literal,
# so we must patch it immediately after importing torch
import sys
import torch

# Workaround for torch.int1/int2 compatibility issue
# Some PyTorch 2.5+ builds don't include torch.int1/int2 (especially CUDA builds)
# torchao uses these in dictionary mappings at import time, so we must patch them first

def create_int_dtype(name):
    """Create a placeholder dtype for missing torch.int types."""
    class IntDType:
        """Placeholder for torch int dtype."""
        def __init__(self, dtype_name):
            self.dtype_name = dtype_name
        def __repr__(self):
            return f"torch.{self.dtype_name}"
        def __str__(self):
            return f"torch.{self.dtype_name}"
        def __hash__(self):
            return hash(f"torch.{self.dtype_name}")
        def __eq__(self, other):
            return isinstance(other, IntDType) and other.dtype_name == self.dtype_name or str(other) == f"torch.{self.dtype_name}"
    return IntDType(name)

# Patch all missing int types that torchao might use
missing_types = []
for int_type in ['int1', 'int2', 'int4']:
    if not hasattr(torch, int_type):
        setattr(torch, int_type, create_int_dtype(int_type))
        sys.modules['torch'].__dict__[int_type] = getattr(torch, int_type)
        missing_types.append(int_type)

if missing_types:
    print(f"Warning: torch types {missing_types} not available in this PyTorch build")
    print("Applying workaround before unsloth/torchao imports...")
    print(f"Workaround applied: {', '.join(f'torch.{t}' for t in missing_types)} placeholders created")

# Now safe to import other modules
import os
import json
import wandb
from pathlib import Path
from datasets import load_dataset
from unsloth import FastLanguageModel, is_bfloat16_supported
from trl import SFTTrainer
from transformers import TrainingArguments
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Hardcoded Configuration
MODEL_NAME = "Qwen/Qwen3-1.7B"  # Fixed model
DATA_DIR = Path("data")  # Fixed data directory
OUTPUT_DIR = Path("output_model")
MAX_SEQ_LENGTH = 2048
BATCH_SIZE = 4  # Adjust based on GPU memory
GRADIENT_ACCUMULATION_STEPS = 4
NUM_EPOCHS = 3
LEARNING_RATE = 2e-4
WARMUP_STEPS = 50
LOGGING_STEPS = 10
SAVE_STEPS = 500
EVAL_STEPS = 500

# WandB and HuggingFace setup (only these are from environment)
WANDB_PROJECT = "qwen3-1.7b-finetune"  # Hardcoded
HF_TOKEN = os.getenv("HF_TOKEN", "")
WANDB_API_KEY = os.getenv("WANDB_API_KEY", "")
# Model upload disabled by default (set HF_MODEL_ID in .env if you want to upload)
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "")

def load_training_data(data_dir: Path):
    """Load JSONL training data."""
    train_path = data_dir / "train.jsonl"
    val_path = data_dir / "val.jsonl"
    
    def load_jsonl(file_path):
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    
    train_data = load_jsonl(train_path)
    val_data = load_jsonl(val_path) if val_path.exists() else []
    
    print(f"Loaded {len(train_data)} training examples")
    if val_data:
        print(f"Loaded {len(val_data)} validation examples")
    
    return train_data, val_data

def main():
    # Initialize WandB
    if WANDB_API_KEY:
        wandb.login(key=WANDB_API_KEY)
    
    wandb.init(
        project=WANDB_PROJECT,
        config={
            "model": MODEL_NAME,
            "max_seq_length": MAX_SEQ_LENGTH,
            "batch_size": BATCH_SIZE,
            "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
            "num_epochs": NUM_EPOCHS,
            "learning_rate": LEARNING_RATE,
        }
    )
    
    print("=" * 80)
    print("Loading model with Unsloth...")
    print("=" * 80)
    
    # Load model with Unsloth (4-bit quantization for efficiency)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detect
        load_in_4bit=True,  # 4-bit quantization
        token=HF_TOKEN if HF_TOKEN else None,
    )
    
    # Enable gradient checkpointing for memory efficiency
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # LoRA rank
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=True,
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )
    
    # Set up tokenizer
    tokenizer = FastLanguageModel.get_tokenizer(model)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    print("=" * 80)
    print("Loading training data...")
    print("=" * 80)
    
    # Load training data
    train_data, val_data = load_training_data(DATA_DIR)
    
    # Convert to dataset format
    def format_dataset(examples):
        """Format examples for training."""
        formatted = []
        for ex in examples:
            messages = ex.get("messages", [])
            # Convert messages to chat format
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
            formatted.append({"text": text})
        return formatted
    
    train_formatted = format_dataset(train_data)
    val_formatted = format_dataset(val_data) if val_data else None
    
    # Create datasets
    from datasets import Dataset
    train_dataset = Dataset.from_list(train_formatted)
    val_dataset = Dataset.from_list(val_formatted) if val_formatted else None
    
    print(f"Training dataset size: {len(train_dataset)}")
    if val_dataset:
        print(f"Validation dataset size: {len(val_dataset)}")
    
    # Training arguments
    training_args = TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        warmup_steps=WARMUP_STEPS,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        fp16=not is_bfloat16_supported(),  # Use bfloat16 if supported, else fp16
        bf16=is_bfloat16_supported(),
        logging_steps=LOGGING_STEPS,
        optim="adamw_8bit",  # 8-bit optimizer for memory efficiency
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir=str(OUTPUT_DIR),
        save_strategy="steps",
        save_steps=SAVE_STEPS,
        evaluation_strategy="steps" if val_dataset else "no",
        eval_steps=EVAL_STEPS if val_dataset else None,
        report_to="wandb",
        load_best_model_at_end=True if val_dataset else False,
        metric_for_best_model="loss" if val_dataset else None,
    )
    
    # Create trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        packing=False,  # Set to True for better efficiency if sequences are short
        args=training_args,
    )
    
    print("=" * 80)
    print("Starting training...")
    print("=" * 80)
    
    # Train
    trainer_stats = trainer.train()
    
    print("=" * 80)
    print("Training complete!")
    print("=" * 80)
    
    # Save model
    print("Saving model...")
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    
    # Save to HuggingFace Hub (only if HF_MODEL_ID is explicitly set)
    if HF_TOKEN and HF_MODEL_ID:
        print(f"Pushing to HuggingFace Hub: {HF_MODEL_ID}")
        model.push_to_hub(HF_MODEL_ID, token=HF_TOKEN)
        tokenizer.push_to_hub(HF_MODEL_ID, token=HF_TOKEN)
    elif HF_TOKEN:
        print("Note: Model saved locally. Set HF_MODEL_ID in .env to upload to HuggingFace Hub.")
    
    # Finish WandB run
    wandb.finish()
    
    print("=" * 80)
    print("Fine-tuning complete!")
    print(f"Model saved to: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
