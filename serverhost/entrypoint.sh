#!/bin/bash
# Entrypoint wrapper for llama-server that ensures models are initialized

set -e

MODELS_DIR="/models"
INIT_SCRIPT="${MODELS_DIR}/init-models.sh"

echo "=========================================="
echo "llama-server Entrypoint"
echo "=========================================="

# Run model initialization if script exists
if [ -f "${INIT_SCRIPT}" ]; then
    echo "Running model initialization..."
    chmod +x "${INIT_SCRIPT}"
    bash "${INIT_SCRIPT}" || {
        echo "⚠️  Model initialization had issues, but continuing..."
    }
else
    echo "⚠️  Init script not found at ${INIT_SCRIPT}"
    echo "Checking for models..."
    
    # Fallback: check if current.gguf exists
    if [ ! -e "${MODELS_DIR}/current.gguf" ]; then
        echo "⚠️  No current.gguf found, looking for any .gguf file..."
        FIRST_MODEL=$(find "${MODELS_DIR}" -maxdepth 1 -name "*.gguf" -type f | head -1)
        if [ -n "${FIRST_MODEL}" ]; then
            MODEL_NAME=$(basename "${FIRST_MODEL}")
            echo "📦 Found model: ${MODEL_NAME}, creating symlink..."
            ln -sf "${MODEL_NAME}" "${MODELS_DIR}/current.gguf"
        else
            echo "❌ No models found! Please upload a model via Upload UI (port 3000)"
            echo "⚠️  Server will start but may fail to load model"
        fi
    fi
fi

# Verify model exists before starting
if [ ! -e "${MODELS_DIR}/current.gguf" ]; then
    echo "❌ ERROR: current.gguf not found!"
    echo "Please upload a model via http://localhost:3000"
    exit 1
fi

echo ""
echo "Starting llama-server..."
echo "=========================================="

# Execute llama-server with all arguments from docker-compose
# Use a wrapper approach to ensure proper argument handling

# Build the command array
CMD=(llama-server)

# Add all arguments if provided
if [ $# -gt 0 ]; then
    for arg in "$@"; do
        # Only add non-empty arguments
        if [ -n "$arg" ]; then
            CMD+=("$arg")
        fi
    done
fi

# Execute the command
echo "Executing: ${CMD[*]}"
exec "${CMD[@]}"

