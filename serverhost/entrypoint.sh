#!/bin/bash
# Entrypoint wrapper for llama-server

set -e

MODELS_DIR="/models"

echo "=========================================="
echo "llama-server Entrypoint"
echo "=========================================="

# Find llama-server binary (it might be in different locations)
LLAMA_SERVER=""
for path in "/usr/local/bin/llama-server" "/app/llama-server" "/llama-server" "llama-server"; do
    if command -v "$path" >/dev/null 2>&1; then
        LLAMA_SERVER="$path"
        break
    fi
done

if [ -z "$LLAMA_SERVER" ]; then
    # Try to find it in common locations
    if [ -f "/usr/local/bin/llama-server" ]; then
        LLAMA_SERVER="/usr/local/bin/llama-server"
    elif [ -f "/app/llama-server" ]; then
        LLAMA_SERVER="/app/llama-server"
    else
        echo "❌ ERROR: llama-server binary not found!"
        echo "Searching for llama-server..."
        find / -name "llama-server" -type f 2>/dev/null | head -5
        exit 1
    fi
fi

echo "✓ Found llama-server at: $LLAMA_SERVER"

# Check for models
echo ""
echo "Checking for models in ${MODELS_DIR}..."
ls -lh "${MODELS_DIR}"/*.gguf 2>/dev/null || echo "⚠️  No .gguf files found"

# Check if model file exists (from command arguments)
MODEL_PATH=""
for i in $(seq 1 $#); do
    arg="${!i}"
    if [ "$arg" = "-m" ] || [ "$arg" = "--model" ]; then
        # Next argument is the model path
        if [ $i -lt $# ]; then
            next_i=$((i + 1))
            MODEL_PATH="${!next_i}"
            break
        fi
    elif [[ "$arg" == *.gguf ]] && [ -z "$MODEL_PATH" ]; then
        # This might be the model path
        if [ -f "$arg" ]; then
            MODEL_PATH="$arg"
            break
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

# Verify model exists if specified
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
    exec "$LLAMA_SERVER"
else
    echo "Starting llama-server with ${#ARGS[@]} arguments"
    exec "$LLAMA_SERVER" "${ARGS[@]}"
fi

