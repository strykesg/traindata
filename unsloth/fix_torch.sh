#!/bin/bash
# Quick fix script for PyTorch compatibility issue

echo "=========================================="
echo "Fixing PyTorch compatibility issue"
echo "=========================================="

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Upgrading PyTorch to 2.5.0+ (required for unsloth)..."
pip install --upgrade torch>=2.5.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo ""
echo "Verifying PyTorch version..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Has int1: {hasattr(torch, \"int1\")}')"

echo ""
echo "=========================================="
echo "Fix complete! Try running train.py again."
echo "=========================================="

