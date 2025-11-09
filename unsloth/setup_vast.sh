#!/bin/bash
# Setup script for vast.ai GTX 5090 instance

set -e

echo "=========================================="
echo "Setting up Qwen3-1.7B Fine-tuning Environment"
echo "=========================================="

# Collect environment variables
echo ""
echo "Please provide the following information:"
echo ""

# Required: HuggingFace Token
read -sp "HuggingFace API Token (required): " HF_TOKEN
echo ""
if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HuggingFace token is required!"
    exit 1
fi

# Optional: WandB API Key
read -sp "WandB API Key (optional, press Enter to skip): " WANDB_API_KEY
echo ""

# Create .env file with hardcoded defaults
echo ""
echo "Creating .env file with hardcoded configuration..."
cat > .env << EOF
# HuggingFace Configuration
HF_TOKEN=$HF_TOKEN
HF_USERNAME=
HF_MODEL_ID=

# WandB Configuration
WANDB_API_KEY=$WANDB_API_KEY
WANDB_PROJECT=qwen3-1.7b-finetune

# Data Configuration
DATA_DIR=data

# Model Configuration (hardcoded)
MODEL_NAME=Qwen/Qwen3-1.7B
EOF

echo ".env file created successfully!"
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get install -y git python3-pip python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch with CUDA support (for A100, use CUDA 12.1 or 12.4)
echo "Installing PyTorch 2.5.1 with CUDA 12.1 support..."
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Verify installation
echo "Verifying installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# Apply torchao compatibility patch
echo ""
echo "Applying torchao compatibility patch..."
python fix_torchao.py
if [ $? -eq 0 ]; then
    echo "✓ Compatibility patch applied successfully"
else
    echo "Note: Patch will be applied automatically when you run training"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Environment variables saved to .env file"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Load environment variables:"
echo "   source .env"
echo "   # Or use: export \$(cat .env | xargs)"
echo ""
echo "3. Run training:"
echo "   python train.py"
echo ""
echo "Or use the quickstart script:"
echo "   bash quickstart.sh"
echo "=========================================="

