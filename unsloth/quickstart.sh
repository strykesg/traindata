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

# Set defaults
export DATA_DIR=${DATA_DIR:-"data"}
export WANDB_PROJECT=${WANDB_PROJECT:-"qwen3-1.7b-finetune"}

echo "Configuration:"
echo "  Model: Qwen/Qwen3-1.7B"
echo "  Data directory: $DATA_DIR"
echo "  WandB project: $WANDB_PROJECT"
if [ -n "$HF_USERNAME" ]; then
    echo "  HF Username: $HF_USERNAME"
fi
if [ -n "$HF_MODEL_ID" ]; then
    echo "  HF Model ID: $HF_MODEL_ID"
fi
echo ""

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "ERROR: Data directory '$DATA_DIR' not found"
    echo "Please ensure training data exists in $DATA_DIR/"
    exit 1
fi

# Check if train.jsonl exists
if [ ! -f "$DATA_DIR/train.jsonl" ]; then
    echo "ERROR: $DATA_DIR/train.jsonl not found"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run training
echo "Starting training..."
python train.py

echo "=========================================="
echo "Training complete!"
echo "=========================================="

