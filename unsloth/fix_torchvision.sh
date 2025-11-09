#!/bin/bash
# Fix torchvision compatibility with PyTorch

set -e

echo "=========================================="
echo "Fixing PyTorch/torchvision compatibility"
echo "=========================================="
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

# Get current PyTorch version
TORCH_VERSION=$(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "not installed")
echo "Current PyTorch version: $TORCH_VERSION"
echo ""

# Uninstall ALL torch-related packages to avoid conflicts
echo "Step 1: Cleaning up PyTorch packages..."
pip uninstall -y torch torchvision torchaudio torchao || true

# Install compatible PyTorch + torchvision + torchaudio together
echo ""
echo "Step 2: Installing PyTorch 2.5.1 with matching torchvision (CUDA 12.1)..."
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# Reinstall unsloth
echo ""
echo "Step 3: Reinstalling unsloth..."
pip install --upgrade --force-reinstall "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Verify installation
echo ""
echo "Step 4: Verifying installation..."
python -c "
import torch
import torchvision
print(f'✓ PyTorch version: {torch.__version__}')
print(f'✓ torchvision version: {torchvision.__version__}')
print(f'✓ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ CUDA device: {torch.cuda.get_device_name(0)}')
print(f'✓ torch.int1 exists: {hasattr(torch, \"int1\")}')

# Test torchvision import
try:
    from torchvision.transforms import InterpolationMode
    print('✓ torchvision imports successfully')
except Exception as e:
    print(f'✗ torchvision import failed: {e}')
"

echo ""
echo "=========================================="
echo "Fix complete!"
echo "=========================================="
echo ""
echo "You can now run:"
echo "  python train.py"
echo ""

