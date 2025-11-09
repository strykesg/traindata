#!/usr/bin/env python3
"""
Export fine-tuned model and prepare for quantization.
This script runs on the training server after training completes.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("Model Export and Preparation Script")
print("=" * 80)

# Configuration
OUTPUT_MODEL_DIR = Path("output_model")
EXPORT_DIR = Path("finetunedmodels")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
MODEL_NAME = f"qwen3-1.7b-trading-bot-{TIMESTAMP}"
FINAL_DIR = EXPORT_DIR / MODEL_NAME

# Create export directory
EXPORT_DIR.mkdir(exist_ok=True)
FINAL_DIR.mkdir(exist_ok=True)

print(f"\n📦 Exporting model to: {FINAL_DIR}")

# Step 1: Check if training output exists
print("\n🔍 Step 1: Checking for trained model...")
if not OUTPUT_MODEL_DIR.exists():
    print(f"❌ Error: {OUTPUT_MODEL_DIR} does not exist!")
    print("   Make sure training has completed successfully.")
    exit(1)

print(f"✓ Found model directory: {OUTPUT_MODEL_DIR}")

# Step 2: Copy the full model
print(f"\n📋 Step 2: Copying full model files...")
try:
    # Copy all model files
    for item in OUTPUT_MODEL_DIR.iterdir():
        if item.is_file():
            shutil.copy2(item, FINAL_DIR / item.name)
            print(f"   ✓ Copied: {item.name}")
        elif item.is_dir() and item.name != "__pycache__":
            shutil.copytree(item, FINAL_DIR / item.name, dirs_exist_ok=True)
            print(f"   ✓ Copied directory: {item.name}")
    
    print(f"✓ Model files copied successfully")
except Exception as e:
    print(f"❌ Error copying files: {e}")
    exit(1)

# Step 3: Create model card
print(f"\n📝 Step 3: Creating model card...")
model_card = f"""# {MODEL_NAME}

## Model Details
- **Base Model**: Qwen/Qwen3-1.7B
- **Fine-tuned**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Training Data**: 15k examples (10k trading + 3k tool-calling + 2k general)
- **Method**: LoRA fine-tuning with Unsloth
- **Hardware**: NVIDIA A100-SXM4-40GB

## Training Configuration
- Batch Size: 8
- Gradient Accumulation: 4 (effective batch size: 32)
- Learning Rate: 2e-4
- Epochs: 3
- LoRA Rank: 16
- Flash Attention 2: Enabled
- Packing: Enabled

## Dataset Composition
- **Trading Examples (66.7%)**: Domain-specific trading decision making
- **Tool-Calling Examples (20%)**: Function calling and tool use
- **General Reasoning (13.3%)**: Broad instruction following

## Usage
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("{FINAL_DIR}")
tokenizer = AutoTokenizer.from_pretrained("{FINAL_DIR}")

messages = [
    {{"role": "user", "content": "Your trading question here"}}
]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## Quantization
This model has been quantized to Q4_K_M GGUF format for efficient inference.
See `{MODEL_NAME}-Q4_K_M.gguf` for the quantized version.

## Notes
- Maintains tool-calling capabilities
- Specialized for trading decisions with reasoning
- Optimized for inference on consumer hardware (quantized version)
"""

with open(FINAL_DIR / "MODEL_CARD.md", 'w') as f:
    f.write(model_card)
print("✓ Model card created")

# Step 4: Create a config file with metadata
print(f"\n⚙️  Step 4: Creating metadata...")
import json
metadata = {
    "model_name": MODEL_NAME,
    "base_model": "Qwen/Qwen3-1.7B",
    "export_date": datetime.now().isoformat(),
    "training_examples": 15000,
    "training_config": {
        "batch_size": 8,
        "gradient_accumulation": 4,
        "learning_rate": 2e-4,
        "epochs": 3,
        "lora_rank": 16,
        "flash_attention_2": True,
        "packing": True
    },
    "dataset_composition": {
        "trading": 10000,
        "tool_calling": 3000,
        "general": 2000
    }
}

with open(FINAL_DIR / "metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)
print("✓ Metadata saved")

# Step 5: Calculate size
print(f"\n💾 Step 5: Calculating model size...")
def get_dir_size(path):
    total = 0
    for entry in path.rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    return total

size_bytes = get_dir_size(FINAL_DIR)
size_gb = size_bytes / (1024**3)
print(f"✓ Total model size: {size_gb:.2f} GB")

print("\n" + "=" * 80)
print("✅ Model export complete!")
print("=" * 80)
print(f"\nExported model location: {FINAL_DIR}")
print(f"Model size: {size_gb:.2f} GB")
print(f"\nNext steps:")
print(f"1. Run quantization: python quantize_model.py")
print(f"2. Download: bash download_model.sh")
print("=" * 80)

