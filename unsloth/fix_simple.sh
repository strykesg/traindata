#!/bin/bash
# Simple fix - downgrade torch and torchvision to compatible versions

set -e

echo "=========================================="
echo "Simple PyTorch/torchvision fix"
echo "=========================================="
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: No virtual environment detected!"
    echo "Please activate your venv first:"
    echo "  source venv/bin/activate"
    exit 1
fi

echo "Current environment: $VIRTUAL_ENV"
echo ""

# Show current versions
echo "Current versions:"
python -c "import torch; print(f'PyTorch: {torch.__version__}')" || echo "PyTorch: not importable"
python -c "import torchvision; print(f'torchvision: {torchvision.__version__}')" || echo "torchvision: not importable"
echo ""

# Force downgrade torch to 2.5.1
echo "Forcing PyTorch downgrade to 2.5.1..."
pip install --force-reinstall torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

echo ""
echo "Verifying installation..."
python -c "
import torch
import torchvision
print(f'✓ PyTorch: {torch.__version__}')
print(f'✓ torchvision: {torchvision.__version__}')
print(f'✓ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ GPU: {torch.cuda.get_device_name(0)}')

# Test imports
try:
    from torchvision.transforms import InterpolationMode
    print('✓ torchvision imports work')
except Exception as e:
    print(f'✗ torchvision import failed: {e}')
    exit(1)

try:
    from unsloth import FastLanguageModel
    print('✓ unsloth imports work')
except Exception as e:
    print(f'✗ unsloth import failed: {e}')
    print('  (This might be OK, will try training anyway)')
"

echo ""
echo "=========================================="
echo "Fix complete!"
echo "=========================================="
echo ""
echo "Try running:"
echo "  python train.py"
echo ""

