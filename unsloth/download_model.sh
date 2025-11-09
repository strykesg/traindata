#!/bin/bash
# Download fine-tuned and quantized model from vast.ai server
# Run this script on your LOCAL machine

set -e

echo "================================================================================"
echo "Download Fine-tuned Model from Server"
echo "================================================================================"

# Configuration - UPDATE THESE IF YOUR SERVER DETAILS CHANGE
SERVER_HOST="157.90.56.162"
SERVER_PORT="32613"
SERVER_USER="root"
REMOTE_DIR="/workspace/traindata/unsloth/finetunedmodels"
LOCAL_DIR="./downloaded_models"

# Create local directory
mkdir -p "$LOCAL_DIR"

echo ""
echo "🔍 Step 1: Finding latest model on server..."
LATEST_MODEL=$(ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
    "ls -td ${REMOTE_DIR}/qwen3-1.7b-trading-bot-* 2>/dev/null | head -1")

if [ -z "$LATEST_MODEL" ]; then
    echo "❌ Error: No model found on server"
    echo "   Make sure export_and_quantize.py has been run"
    exit 1
fi

MODEL_NAME=$(basename "$LATEST_MODEL")
echo "✓ Found model: ${MODEL_NAME}"

# Check what files exist
echo ""
echo "📋 Step 2: Checking available files..."
ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
    "ls -lh ${LATEST_MODEL}/*.gguf ${LATEST_MODEL}/*.md ${LATEST_MODEL}/*.json 2>/dev/null || echo 'No GGUF files found yet'"

# Ask user what to download
echo ""
echo "📦 What would you like to download?"
echo "   1) Full model + Q4_K_M quantized (recommended)"
echo "   2) Q4_K_M quantized only (smallest, fastest)"
echo "   3) Full model only (largest)"
echo "   4) Everything (full + FP16 GGUF + Q4_K_M)"
echo ""
read -p "Enter choice [1-4]: " CHOICE

case $CHOICE in
    1)
        FILES="*.safetensors *.json config.json tokenizer* *Q4_K_M.gguf *.md"
        DESC="Full model + Q4_K_M quantized"
        ;;
    2)
        FILES="*Q4_K_M.gguf tokenizer* config.json *.md *.json"
        DESC="Q4_K_M quantized only"
        ;;
    3)
        FILES="*.safetensors *.json config.json tokenizer* *.md"
        DESC="Full model only"
        ;;
    4)
        FILES="*"
        DESC="Everything"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📥 Step 3: Downloading ${DESC}..."
echo "   This may take a while..."

# Create local model directory
LOCAL_MODEL_DIR="${LOCAL_DIR}/${MODEL_NAME}"
mkdir -p "$LOCAL_MODEL_DIR"

# Download with progress
echo ""
echo "   Destination: ${LOCAL_MODEL_DIR}"
echo ""

# Use rsync for better progress and resume capability
rsync -avz --progress \
    -e "ssh -p ${SERVER_PORT}" \
    --include="${FILES}" \
    --exclude="*" \
    ${SERVER_USER}@${SERVER_HOST}:${LATEST_MODEL}/ \
    "${LOCAL_MODEL_DIR}/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Download complete!"
else
    echo ""
    echo "❌ Download failed or incomplete"
    exit 1
fi

# Calculate downloaded size
TOTAL_SIZE=$(du -sh "${LOCAL_MODEL_DIR}" | cut -f1)

echo ""
echo "================================================================================"
echo "✅ Model Downloaded Successfully!"
echo "================================================================================"
echo ""
echo "📁 Location: ${LOCAL_MODEL_DIR}"
echo "💾 Total size: ${TOTAL_SIZE}"
echo ""
echo "📋 Downloaded files:"
ls -lh "${LOCAL_MODEL_DIR}"
echo ""
echo "🚀 Quick start:"
echo ""

# Check if Q4_K_M exists and provide usage instructions
if ls "${LOCAL_MODEL_DIR}"/*Q4_K_M.gguf 1> /dev/null 2>&1; then
    GGUF_FILE=$(ls "${LOCAL_MODEL_DIR}"/*Q4_K_M.gguf | head -1)
    GGUF_NAME=$(basename "$GGUF_FILE")
    echo "Using quantized model with llama.cpp:"
    echo "  ./llama-cli -m \"${LOCAL_MODEL_DIR}/${GGUF_NAME}\" -p \"Your prompt\" -n 512"
    echo ""
fi

if ls "${LOCAL_MODEL_DIR}"/*.safetensors 1> /dev/null 2>&1; then
    echo "Using full model with transformers:"
    echo "  from transformers import AutoModelForCausalLM, AutoTokenizer"
    echo "  model = AutoModelForCausalLM.from_pretrained('${LOCAL_MODEL_DIR}')"
    echo "  tokenizer = AutoTokenizer.from_pretrained('${LOCAL_MODEL_DIR}')"
    echo ""
fi

echo "📖 See MODEL_CARD.md for detailed usage instructions"
echo "================================================================================"

# Optional: Create a local usage script
cat > "${LOCAL_MODEL_DIR}/test_model.py" << 'EOF'
#!/usr/bin/env python3
"""
Quick test script for the downloaded model.
"""
import os
from pathlib import Path

model_dir = Path(__file__).parent

print("Testing fine-tuned model...")
print(f"Model directory: {model_dir}")

# Check for GGUF file
gguf_files = list(model_dir.glob("*Q4_K_M.gguf"))
if gguf_files:
    print(f"\n✓ Found quantized model: {gguf_files[0].name}")
    print("\nTo use with llama-cpp-python:")
    print("  pip install llama-cpp-python")
    print("  from llama_cpp import Llama")
    print(f"  llm = Llama(model_path='{gguf_files[0]}')")

# Check for full model
safetensors = list(model_dir.glob("*.safetensors"))
if safetensors:
    print(f"\n✓ Found full model files")
    print("\nTo use with transformers:")
    print("  from transformers import AutoModelForCausalLM, AutoTokenizer")
    print(f"  model = AutoModelForCausalLM.from_pretrained('{model_dir}')")
    print(f"  tokenizer = AutoTokenizer.from_pretrained('{model_dir}')")

print("\n" + "="*60)
EOF

chmod +x "${LOCAL_MODEL_DIR}/test_model.py"
echo ""
echo "💡 Tip: Run 'python ${LOCAL_MODEL_DIR}/test_model.py' to test the model"

