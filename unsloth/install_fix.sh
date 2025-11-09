#!/bin/bash
# Alternative installation fix - try PyTorch nightly or reinstall torchao

echo "=========================================="
echo "Alternative Fix for torch.int1 Issue"
echo "=========================================="

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Option 1: Try PyTorch nightly build (may have torch.int1)"
read -p "Install PyTorch nightly? (y/n): " install_nightly

if [ "$install_nightly" = "y" ]; then
    echo "Installing PyTorch nightly..."
    pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu121
fi

echo ""
echo "Option 2: Reinstall torchao"
read -p "Reinstall torchao? (y/n): " reinstall_torchao

if [ "$reinstall_torchao" = "y" ]; then
    echo "Uninstalling torchao..."
    pip uninstall -y torchao
    echo "Reinstalling torchao..."
    pip install torchao
fi

echo ""
echo "Verifying..."
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'Has int1: {hasattr(torch, \"int1\")}')"

echo ""
echo "=========================================="
echo "If torch.int1 still not available, train.py has a workaround."
echo "Try running: python train.py"
echo "=========================================="

