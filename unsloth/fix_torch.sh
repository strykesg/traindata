#!/bin/bash
# Quick fix script for PyTorch compatibility issue

echo "=========================================="
echo "Fixing PyTorch compatibility issue"
echo "=========================================="

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Checking PyTorch version..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'Has int1: {hasattr(torch, \"int1\")}')"

echo ""
echo "Note: Some PyTorch 2.5+ builds don't include torch.int1."
echo "The train.py script includes a workaround for this."
echo ""
echo "If you still get errors, try:"
echo "1. Reinstall PyTorch from nightly build:"
echo "   pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu121"
echo ""
echo "2. Or use the workaround in train.py (already included)"
echo ""
echo "=========================================="
echo "Try running train.py - it should work with the workaround."
echo "=========================================="

