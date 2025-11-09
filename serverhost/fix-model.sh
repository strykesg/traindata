#!/bin/bash
# Quick fix script to ensure model is in the right place

set -e

echo "=========================================="
echo "Model Fix Script"
echo "=========================================="
echo ""

MODELS_DIR="./models"
MODEL_NAME="qwen3-1.7b-trading-Q4_K_M.gguf"

# Create models directory if it doesn't exist
mkdir -p "$MODELS_DIR"

echo "1. Checking for model file..."
echo ""

# Check if model exists locally
if [ -f "../finetunedmodels/qwen3-1.7b-trading-q4km/$MODEL_NAME" ]; then
    echo "✓ Found model in finetunedmodels/"
    echo "Copying to serverhost/models/..."
    cp "../finetunedmodels/qwen3-1.7b-trading-q4km/$MODEL_NAME" "$MODELS_DIR/"
    echo "✓ Model copied"
elif [ -f "$MODELS_DIR/$MODEL_NAME" ]; then
    echo "✓ Model already exists in models/"
else
    echo "⚠️  Model not found locally"
    echo "Please ensure the model file exists or upload it via the Upload UI"
fi

echo ""
echo "2. Verifying model file..."
if [ -f "$MODELS_DIR/$MODEL_NAME" ]; then
    SIZE=$(du -h "$MODELS_DIR/$MODEL_NAME" | cut -f1)
    echo "✓ Model found: $MODEL_NAME ($SIZE)"
else
    echo "✗ Model not found: $MODEL_NAME"
    echo ""
    echo "Available files in models/:"
    ls -lh "$MODELS_DIR"/*.gguf 2>/dev/null || echo "  (no .gguf files found)"
fi

echo ""
echo "3. Checking Docker containers..."
if docker compose ps | grep -q "Up"; then
    echo "✓ Containers are running"
    echo ""
    echo "4. Checking models in containers..."
    echo ""
    echo "Upload UI container:"
    docker compose exec upload-ui ls -lh /app/models/*.gguf 2>/dev/null || echo "  (no models found)"
    echo ""
    echo "Llama-server container:"
    docker compose exec llama-server ls -lh /models/*.gguf 2>/dev/null || echo "  (no models found)"
else
    echo "⚠️  Containers are not running"
    echo "Start them with: docker compose up -d"
fi

echo ""
echo "=========================================="
echo "Fix complete"
echo "=========================================="
echo ""
echo "If model is missing, you can:"
echo "1. Copy it manually: cp /path/to/model.gguf $MODELS_DIR/"
echo "2. Upload via UI: http://localhost:3000"
echo "3. Restart containers: docker compose restart"

