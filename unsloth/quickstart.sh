#!/bin/bash
# Quick start script for vast.ai deployment

set -e

echo "=========================================="
echo "Qwen3-1.7B Fine-tuning Quick Start"
echo "=========================================="

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "WARNING: .env file not found. Using environment variables or defaults."
fi

# Check for required environment variables
if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HF_TOKEN environment variable not set"
    echo "Set it with: export HF_TOKEN='your_token'"
    echo "Or run: bash setup_vast.sh to create .env file"
    exit 1
fi

if [ -z "$WANDB_API_KEY" ]; then
    echo "WARNING: WANDB_API_KEY not set. WandB logging will be disabled."
fi

echo "Configuration (hardcoded):"
echo "  Model: Qwen/Qwen3-1.7B"
echo "  Data directory: data"
echo "  WandB project: qwen3-1.7b-finetune"
echo ""

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "ERROR: Data directory 'data' not found"
    echo "Please ensure training data exists in data/"
    exit 1
fi

# Check if train.jsonl exists
if [ ! -f "data/train.jsonl" ]; then
    echo "ERROR: data/train.jsonl not found"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Fix torchao compatibility if needed
echo ""
echo "Checking torchao compatibility..."
python fix_torchao.py
if [ $? -ne 0 ]; then
    echo "Warning: Could not patch torchao automatically"
    echo "You may need to run: python fix_torchao.py manually"
fi

# Run training
echo ""
echo "Starting training..."
python train.py

echo "=========================================="
echo "Training complete!"
echo "=========================================="

