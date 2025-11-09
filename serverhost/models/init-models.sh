#!/bin/bash
# Initialize models directory and restore active model on startup

set -e

MODELS_DIR="/models"
CURRENT_LINK="${MODELS_DIR}/current.gguf"
STATE_FILE="${MODELS_DIR}/.active_model"

echo "=========================================="
echo "Model Initialization Script"
echo "=========================================="

# Ensure models directory exists
mkdir -p "${MODELS_DIR}"

# Check if current.gguf symlink exists
if [ ! -e "${CURRENT_LINK}" ]; then
    echo "⚠️  No active model found (current.gguf missing)"
    
    # Try to restore from state file
    if [ -f "${STATE_FILE}" ]; then
        ACTIVE_MODEL=$(cat "${STATE_FILE}")
        echo "📋 Found saved state: ${ACTIVE_MODEL}"
        
        if [ -f "${MODELS_DIR}/${ACTIVE_MODEL}" ]; then
            echo "✅ Restoring active model: ${ACTIVE_MODEL}"
            ln -sf "${ACTIVE_MODEL}" "${CURRENT_LINK}"
            echo "✓ Active model restored successfully"
        else
            echo "⚠️  Saved model ${ACTIVE_MODEL} not found, checking for any .gguf file..."
            
            # Find first available model
            FIRST_MODEL=$(find "${MODELS_DIR}" -maxdepth 1 -name "*.gguf" -type f | head -1)
            if [ -n "${FIRST_MODEL}" ]; then
                MODEL_NAME=$(basename "${FIRST_MODEL}")
                echo "📦 Found model: ${MODEL_NAME}"
                echo "🔗 Setting as active model..."
                ln -sf "${MODEL_NAME}" "${CURRENT_LINK}"
                echo "${MODEL_NAME}" > "${STATE_FILE}"
                echo "✓ Active model set to: ${MODEL_NAME}"
            else
                echo "❌ No models found in ${MODELS_DIR}"
                echo "⚠️  Please upload a model via the Upload UI (port 3000)"
                exit 1
            fi
        fi
    else
        echo "📋 No saved state found, checking for available models..."
        
        # Find first available model
        FIRST_MODEL=$(find "${MODELS_DIR}" -maxdepth 1 -name "*.gguf" -type f | head -1)
        if [ -n "${FIRST_MODEL}" ]; then
            MODEL_NAME=$(basename "${FIRST_MODEL}")
            echo "📦 Found model: ${MODEL_NAME}"
            echo "🔗 Setting as active model..."
            ln -sf "${MODEL_NAME}" "${CURRENT_LINK}"
            echo "${MODEL_NAME}" > "${STATE_FILE}"
            echo "✓ Active model set to: ${MODEL_NAME}"
        else
            echo "❌ No models found in ${MODELS_DIR}"
            echo "⚠️  Please upload a model via the Upload UI (port 3000)"
            exit 1
        fi
    fi
else
    # Symlink exists, verify it's valid
    if [ -L "${CURRENT_LINK}" ]; then
        TARGET=$(readlink -f "${CURRENT_LINK}")
        MODEL_NAME=$(basename "${TARGET}")
        
        if [ -f "${TARGET}" ]; then
            echo "✅ Active model found: ${MODEL_NAME}"
            echo "${MODEL_NAME}" > "${STATE_FILE}"
            echo "✓ State file updated"
        else
            echo "⚠️  Symlink target ${TARGET} not found, fixing..."
            rm -f "${CURRENT_LINK}"
            # Re-run initialization
            exec "$0"
        fi
    elif [ -f "${CURRENT_LINK}" ]; then
        # It's a regular file, convert to symlink
        MODEL_NAME=$(basename "${CURRENT_LINK}")
        echo "📋 Found current.gguf as regular file, converting to symlink..."
        mv "${CURRENT_LINK}" "${MODELS_DIR}/${MODEL_NAME}"
        ln -sf "${MODEL_NAME}" "${CURRENT_LINK}"
        echo "${MODEL_NAME}" > "${STATE_FILE}"
        echo "✓ Converted to symlink"
    fi
fi

# Verify final state
if [ -L "${CURRENT_LINK}" ] && [ -f "$(readlink -f "${CURRENT_LINK}")" ]; then
    ACTIVE=$(basename "$(readlink -f "${CURRENT_LINK}")")
    SIZE=$(du -h "$(readlink -f "${CURRENT_LINK}")" | cut -f1)
    echo ""
    echo "=========================================="
    echo "✓ Model Initialization Complete"
    echo "=========================================="
    echo "Active Model: ${ACTIVE}"
    echo "Size: ${SIZE}"
    echo "Path: $(readlink -f "${CURRENT_LINK}")"
    echo "=========================================="
else
    echo "❌ Failed to initialize active model"
    exit 1
fi

