#!/bin/bash
# Startup script for upload-ui container

set -e

MODELS_DIR="${MODELS_DIR:-/app/models}"

echo "=========================================="
echo "Upload UI Startup Script"
echo "=========================================="

# Ensure models directory exists and is writable
echo "Checking models directory: $MODELS_DIR"
mkdir -p "$MODELS_DIR"

if [ ! -w "$MODELS_DIR" ]; then
    echo "❌ ERROR: Models directory is not writable: $MODELS_DIR"
    exit 1
fi

echo "✓ Models directory is ready: $MODELS_DIR"

# List existing models
echo ""
echo "Existing models:"
ls -lh "$MODELS_DIR"/*.gguf 2>/dev/null || echo "  (no models found)"

# Set proper permissions
chmod 755 "$MODELS_DIR" 2>/dev/null || true

echo ""
echo "Starting Flask application..."
echo "=========================================="

# Start Flask app
exec python app.py

