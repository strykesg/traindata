#!/usr/bin/env python3
"""
Create a balanced dataset mixing trading examples with tool-calling examples.
Target: 15k total (10k trading + 3k tool-calling + 2k general)
"""

import json
import random
from pathlib import Path
from datasets import load_dataset
from huggingface_hub import login
import time
from datetime import datetime

# HuggingFace token (from environment variable)
import os
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Start timer
start_time = time.time()
print(f"\n🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("data_balanced")
OUTPUT_DIR.mkdir(exist_ok=True)

# Target counts
TARGET_TRADING = 10000
TARGET_TOOL_CALLING = 3000
TARGET_GENERAL = 2000
TOTAL_TARGET = TARGET_TRADING + TARGET_TOOL_CALLING + TARGET_GENERAL

print("=" * 80)
print("Creating Balanced Dataset for Fine-tuning")
print("=" * 80)
print(f"Target composition:")
print(f"  - Trading examples: {TARGET_TRADING:,}")
print(f"  - Tool-calling examples: {TARGET_TOOL_CALLING:,}")
print(f"  - General reasoning: {TARGET_GENERAL:,}")
print(f"  - Total: {TOTAL_TARGET:,}")
print("=" * 80)

# Login to HuggingFace
print("\n📡 Logging into HuggingFace...")
login(token=HF_TOKEN)
print("✓ Logged in successfully")

# Step 1: Load existing trading data
print("\n📊 Step 1: Loading existing trading data...")
trading_examples = []
for split in ["train", "val", "test"]:
    file_path = DATA_DIR / f"{split}.jsonl"
    if file_path.exists():
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    trading_examples.append(json.loads(line))

print(f"✓ Loaded {len(trading_examples):,} trading examples")

# Step 2: Sample trading data
print(f"\n📉 Step 2: Sampling {TARGET_TRADING:,} trading examples...")
if len(trading_examples) > TARGET_TRADING:
    # Use stratified sampling if possible, otherwise random
    trading_sampled = random.sample(trading_examples, TARGET_TRADING)
else:
    trading_sampled = trading_examples
    print(f"⚠️  Only {len(trading_examples):,} available, using all")

print(f"✓ Selected {len(trading_sampled):,} trading examples")

# Step 3: Download tool-calling datasets
print(f"\n🔧 Step 3: Downloading tool-calling examples ({TARGET_TOOL_CALLING:,})...")

tool_calling_examples = []

# Dataset 1: Glaive Function Calling v2 (high quality)
try:
    print("  📥 Downloading: glaiveai/glaive-function-calling-v2...")
    print("     (This may take a minute...)")
    ds = load_dataset("glaiveai/glaive-function-calling-v2", split="train", streaming=True)
    print("     ✓ Dataset loaded, processing examples...")
    
    count = 0
    last_reported = 0
    for example in ds:
        if count >= TARGET_TOOL_CALLING:
            break
        
        # Convert to our format
        if "system" in example and "chat" in example:
            messages = [
                {"role": "system", "content": example["system"]}
            ]
            # Parse chat history
            chat = example["chat"]
            # Simple parsing - adapt as needed
            if isinstance(chat, str):
                # Try to extract user/assistant turns
                messages.append({"role": "user", "content": chat})
            
            tool_calling_examples.append({"messages": messages})
            count += 1
            
            # Progress reporting every 500 examples
            if count - last_reported >= 500:
                print(f"     ... {count:,} / {TARGET_TOOL_CALLING:,} collected ({count/TARGET_TOOL_CALLING*100:.1f}%)")
                last_reported = count
    
    print(f"  ✓ Added {count:,} examples from glaive-function-calling-v2")
except Exception as e:
    print(f"  ⚠️  Failed to load glaive dataset: {e}")
    import traceback
    print(f"     Full error: {traceback.format_exc()}")

# Dataset 2: NousResearch Hermes Function Calling (if we need more)
if len(tool_calling_examples) < TARGET_TOOL_CALLING:
    try:
        remaining = TARGET_TOOL_CALLING - len(tool_calling_examples)
        print(f"  📥 Downloading: NousResearch/hermes-function-calling-v1 ({remaining:,} more needed)...")
        print("     (This may take a minute...)")
        ds = load_dataset("NousResearch/hermes-function-calling-v1", split="train", streaming=True)
        print("     ✓ Dataset loaded, processing examples...")
        
        count = 0
        last_reported = 0
        for example in ds:
            if count >= remaining:
                break
            
            # Convert to our format
            if "conversations" in example:
                messages = []
                for msg in example["conversations"]:
                    if "from" in msg and "value" in msg:
                        role = "assistant" if msg["from"] == "gpt" else msg["from"]
                        messages.append({"role": role, "content": msg["value"]})
                
                if messages:
                    tool_calling_examples.append({"messages": messages})
                    count += 1
                    
                    # Progress reporting every 250 examples
                    if count - last_reported >= 250:
                        print(f"     ... {count:,} / {remaining:,} collected ({count/remaining*100:.1f}%)")
                        last_reported = count
        
        print(f"  ✓ Added {count:,} examples from hermes-function-calling")
    except Exception as e:
        print(f"  ⚠️  Failed to load hermes dataset: {e}")
        import traceback
        print(f"     Full error: {traceback.format_exc()}")

# Alternative: Try Gorilla OpenFunctions
if len(tool_calling_examples) < TARGET_TOOL_CALLING:
    try:
        remaining = TARGET_TOOL_CALLING - len(tool_calling_examples)
        print(f"  Downloading: gorilla-llm/APIBench ({remaining:,} more)...")
        ds = load_dataset("gorilla-llm/APIBench", split="train", streaming=True)
        
        count = 0
        for example in ds:
            if count >= remaining:
                break
            
            # Convert to our format
            messages = []
            if "question" in example and "api_call" in example:
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant with access to function calling."},
                    {"role": "user", "content": example["question"]},
                    {"role": "assistant", "content": example.get("api_call", "")}
                ]
            
            if messages:
                tool_calling_examples.append({"messages": messages})
                count += 1
        
        print(f"  ✓ Added {count:,} examples from APIBench")
    except Exception as e:
        print(f"  ⚠️  Failed to load APIBench: {e}")

print(f"\n✓ Total tool-calling examples collected: {len(tool_calling_examples):,}")

# Step 4: Download general reasoning/chat examples
print(f"\n💬 Step 4: Downloading general reasoning examples ({TARGET_GENERAL:,})...")

general_examples = []

# Dataset: OpenOrca or similar high-quality instruction following
try:
    print("  📥 Downloading: Open-Orca/OpenOrca subset...")
    print("     (This may take a minute...)")
    ds = load_dataset("Open-Orca/OpenOrca", split="train", streaming=True)
    print("     ✓ Dataset loaded, processing examples...")
    
    count = 0
    last_reported = 0
    for example in ds:
        if count >= TARGET_GENERAL:
            break
        
        # Convert to our format
        if "system_prompt" in example and "question" in example and "response" in example:
            messages = [
                {"role": "system", "content": example["system_prompt"]},
                {"role": "user", "content": example["question"]},
                {"role": "assistant", "content": example["response"]}
            ]
            general_examples.append({"messages": messages})
            count += 1
            
            # Progress reporting every 250 examples
            if count - last_reported >= 250:
                print(f"     ... {count:,} / {TARGET_GENERAL:,} collected ({count/TARGET_GENERAL*100:.1f}%)")
                last_reported = count
    
    print(f"  ✓ Added {count:,} examples from OpenOrca")
except Exception as e:
    print(f"  ⚠️  Failed to load OpenOrca: {e}")
    import traceback
    print(f"     Full error: {traceback.format_exc()}")

print(f"\n✓ Total general examples collected: {len(general_examples):,}")

# Step 5: Combine and shuffle
print(f"\n🔀 Step 5: Combining and shuffling datasets...")

all_examples = trading_sampled + tool_calling_examples + general_examples
random.shuffle(all_examples)

print(f"✓ Total examples: {len(all_examples):,}")
print(f"  - Trading: {len(trading_sampled):,} ({len(trading_sampled)/len(all_examples)*100:.1f}%)")
print(f"  - Tool-calling: {len(tool_calling_examples):,} ({len(tool_calling_examples)/len(all_examples)*100:.1f}%)")
print(f"  - General: {len(general_examples):,} ({len(general_examples)/len(all_examples)*100:.1f}%)")

# Step 6: Split into train/val/test (80/10/10)
print(f"\n📂 Step 6: Creating train/val/test splits (80/10/10)...")

total = len(all_examples)
train_size = int(total * 0.8)
val_size = int(total * 0.1)
test_size = total - train_size - val_size

train_data = all_examples[:train_size]
val_data = all_examples[train_size:train_size + val_size]
test_data = all_examples[train_size + val_size:]

print(f"✓ Train: {len(train_data):,} examples")
print(f"✓ Val: {len(val_data):,} examples")
print(f"✓ Test: {len(test_data):,} examples")

# Step 7: Save datasets
print(f"\n💾 Step 7: Saving balanced datasets...")

for name, data in [("train", train_data), ("val", val_data), ("test", test_data)]:
    output_path = OUTPUT_DIR / f"{name}.jsonl"
    with open(output_path, 'w') as f:
        for example in data:
            f.write(json.dumps(example) + '\n')
    print(f"✓ Saved {output_path} ({len(data):,} examples)")

# Save backup of old data
print(f"\n📦 Creating backup of original data...")
backup_dir = Path("data_original_backup")
backup_dir.mkdir(exist_ok=True)
import shutil
for file in DATA_DIR.glob("*.jsonl"):
    shutil.copy(file, backup_dir / file.name)
print(f"✓ Original data backed up to {backup_dir}/")

elapsed_time = time.time() - start_time
minutes = int(elapsed_time // 60)
seconds = int(elapsed_time % 60)

print("\n" + "=" * 80)
print("✅ Balanced dataset creation complete!")
print("=" * 80)
print(f"\n🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⏱️  Total time: {minutes}m {seconds}s")
print(f"\nNext steps:")
print(f"1. Review the balanced dataset in: {OUTPUT_DIR}/")
print(f"2. Move to data/ directory: mv {OUTPUT_DIR}/* data/")
print(f"3. Commit changes: git add data/ && git commit -m 'Add balanced dataset'")
print(f"4. Push to server or upload directly")
print("=" * 80)

