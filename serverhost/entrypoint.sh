#!/bin/bash
# Entrypoint wrapper for llama-server

set -e

MODELS_DIR="/models"

echo "=========================================="
echo "llama-server Entrypoint"
echo "=========================================="

# Check if model file exists (from command arguments)
MODEL_PATH=""
for arg in "$@"; do
    if [ "$arg" = "-m" ] || [ "$arg" = "--model" ]; then
        # Next argument is the model path
        continue
    elif [[ "$arg" == *.gguf ]] && [ -z "$MODEL_PATH" ]; then
        # This might be the model path
        if [ -f "$arg" ]; then
            MODEL_PATH="$arg"
        fi
    fi
done

# If no model found in args, check for default model
if [ -z "$MODEL_PATH" ]; then
    DEFAULT_MODEL="${MODELS_DIR}/qwen3-1.7b-trading-Q4_K_M.gguf"
    if [ -f "$DEFAULT_MODEL" ]; then
        MODEL_PATH="$DEFAULT_MODEL"
        echo "✓ Found default model: $MODEL_PATH"
    else
        # Try to find any .gguf file
        FIRST_MODEL=$(find "${MODELS_DIR}" -maxdepth 1 -name "*.gguf" -type f 2>/dev/null | head -1)
        if [ -n "$FIRST_MODEL" ]; then
            MODEL_PATH="$FIRST_MODEL"
            echo "✓ Found model: $MODEL_PATH"
        else
            echo "⚠️  No model file found in ${MODELS_DIR}"
            echo "⚠️  Server will start but may fail to load model"
        fi
    fi
else
    echo "✓ Using model from command: $MODEL_PATH"
fi

# Verify model exists
if [ -n "$MODEL_PATH" ] && [ ! -f "$MODEL_PATH" ]; then
    echo "❌ ERROR: Model file not found: $MODEL_PATH"
    exit 1
fi

echo ""
echo "Starting llama-server..."
echo "=========================================="

# Filter out any problematic arguments (like standalone "--")
ARGS=()
for arg in "$@"; do
    # Skip empty arguments or standalone "--"
    if [ -n "$arg" ] && [ "$arg" != "--" ]; then
        ARGS+=("$arg")
    fi
done

# Execute llama-server with filtered arguments
if [ ${#ARGS[@]} -eq 0 ]; then
    echo "No arguments provided, starting with defaults"
    exec llama-server
else
    echo "Starting llama-server with ${#ARGS[@]} arguments"
    exec llama-server "${ARGS[@]}"
fi

