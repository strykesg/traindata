#!/bin/bash
# Debug script for serverhost setup

echo "=========================================="
echo "Serverhost Debug Script"
echo "=========================================="
echo ""

echo "1. Checking local models directory..."
if [ -d "./models" ]; then
    echo "✓ models/ directory exists"
    echo "Contents:"
    ls -lh models/ 2>/dev/null || echo "  (empty or error)"
else
    echo "✗ models/ directory not found"
fi

echo ""
echo "2. Checking Docker containers..."
docker compose ps

echo ""
echo "3. Checking upload-ui logs (last 20 lines)..."
docker compose logs --tail=20 upload-ui 2>/dev/null || echo "No upload-ui logs"

echo ""
echo "4. Checking llama-server logs (last 20 lines)..."
docker compose logs --tail=20 llama-server 2>/dev/null || echo "No llama-server logs"

echo ""
echo "5. Checking models in upload-ui container..."
docker compose exec upload-ui ls -lh /app/models/ 2>/dev/null || echo "Cannot access upload-ui container"

echo ""
echo "6. Checking models in llama-server container..."
docker compose exec llama-server ls -lh /models/ 2>/dev/null || echo "Cannot access llama-server container"

echo ""
echo "7. Testing upload-ui endpoint..."
curl -s http://localhost:3000/api/models | python3 -m json.tool 2>/dev/null || echo "Cannot reach upload-ui API"

echo ""
echo "=========================================="
echo "Debug complete"
echo "=========================================="

