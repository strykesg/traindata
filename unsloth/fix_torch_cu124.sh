#!/bin/bash
# Fix PyTorch version compatibility for torchao/torch.int1 (CUDA 12.4 version)

set -e

echo "=========================================="
echo "Fixing PyTorch compatibility issue (CUDA 12.4)"
echo "=========================================="
echo ""
echo "This will upgrade PyTorch to 2.5.1 with CUDA 12.4 support"
echo "which supports torch.int1 required by the torchao library."
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: No virtual environment detected!"
    echo "Please activate your venv first:"
    echo "  source venv/bin/activate"
    exit 1
fi

echo "Virtual environment: $VIRTUAL_ENV"
echo ""

# Uninstall existing torch packages to avoid conflicts
echo "Step 1: Uninstalling existing PyTorch packages..."
pip uninstall -y torch torchvision torchaudio || true

# Install PyTorch 2.5.1 with CUDA 12.4 support
echo ""
echo "Step 2: Installing PyTorch 2.5.1 with CUDA 12.4 support..."
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Reinstall unsloth and dependencies (they may have been affected)
echo ""
echo "Step 3: Reinstalling unsloth and dependencies..."
pip install --upgrade --force-reinstall --no-deps unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
pip install transformers>=4.51.0 accelerate bitsandbytes peft trl datasets

# Verify installation
echo ""
echo "Step 4: Verifying installation..."
python -c "import torch; print(f'✓ PyTorch version: {torch.__version__}'); print(f'✓ CUDA available: {torch.cuda.is_available()}'); print(f'✓ CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}'); print(f'✓ torch.int1 exists: {hasattr(torch, \"int1\")}')"

echo ""
echo "=========================================="
echo "Fix complete!"
echo "=========================================="
echo ""
echo "You can now run:"
echo "  python train.py"
echo ""

