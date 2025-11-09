#!/bin/bash
# Setup script for vast.ai GTX 5090 instance

set -e

echo "=========================================="
echo "Setting up Qwen3-1.7B Fine-tuning Environment"
echo "=========================================="

# Function to prompt for input with default value
prompt_with_default() {
    local prompt_text=$1
    local default_value=$2
    local var_name=$3
    local is_secret=${4:-false}
    
    if [ "$is_secret" = true ]; then
        read -sp "$prompt_text [$default_value]: " input
        echo ""
    else
        read -p "$prompt_text [$default_value]: " input
    fi
    
    if [ -z "$input" ]; then
        input=$default_value
    fi
    
    eval "$var_name='$input'"
}

# Collect environment variables
echo ""
echo "Please provide the following information:"
echo "(Press Enter to use default values in brackets)"
echo ""

# Required: HuggingFace Token
prompt_with_default "HuggingFace API Token (required)" "" HF_TOKEN true
if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HuggingFace token is required!"
    exit 1
fi

# Optional: WandB API Key
prompt_with_default "WandB API Key (optional, press Enter to skip)" "" WANDB_API_KEY true

# Optional: HuggingFace Username
prompt_with_default "HuggingFace Username (for model upload)" "" HF_USERNAME false

# Optional: WandB Project
prompt_with_default "WandB Project Name" "qwen3-1.7b-finetune" WANDB_PROJECT false

# Optional: Data Directory
prompt_with_default "Data Directory (train.jsonl location)" "data" DATA_DIR false

# Optional: HuggingFace Model ID
if [ -n "$HF_USERNAME" ]; then
    default_model_id="${HF_USERNAME}/qwen3-1.7b-trading-bot"
else
    default_model_id=""
fi
prompt_with_default "HuggingFace Model ID (for upload)" "$default_model_id" HF_MODEL_ID false

# Create .env file
echo ""
echo "Creating .env file..."
cat > .env << EOF
# HuggingFace Configuration
HF_TOKEN=$HF_TOKEN
HF_USERNAME=$HF_USERNAME
HF_MODEL_ID=$HF_MODEL_ID

# WandB Configuration
WANDB_API_KEY=$WANDB_API_KEY
WANDB_PROJECT=$WANDB_PROJECT

# Data Configuration
DATA_DIR=$DATA_DIR
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

# Install PyTorch with CUDA support (adjust CUDA version as needed)
echo "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Verify installation
echo "Verifying installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

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

