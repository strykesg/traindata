#!/bin/bash
# Ensure models directory exists and is properly set up before starting containers

set -e

MODELS_DIR="./models"

echo "=========================================="
echo "Ensuring Models Directory"
echo "=========================================="

# Create directory if it doesn't exist
if [ ! -d "$MODELS_DIR" ]; then
    echo "Creating models directory: $MODELS_DIR"
    mkdir -p "$MODELS_DIR"
else
    echo "✓ Models directory exists: $MODELS_DIR"
fi

# Ensure it's writable
chmod 755 "$MODELS_DIR"
echo "✓ Set directory permissions"

# Create .gitkeep if it doesn't exist (prevents git from removing empty directory)
if [ ! -f "$MODELS_DIR/.gitkeep" ]; then
    touch "$MODELS_DIR/.gitkeep"
    echo "✓ Created .gitkeep"
fi

# List current contents
echo ""
echo "Current contents:"
ls -lah "$MODELS_DIR" | head -20 || echo "  (empty or error)"

echo ""
echo "=========================================="
echo "Directory ready"
echo "=========================================="

