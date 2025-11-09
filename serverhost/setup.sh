#!/bin/bash
# llama.cpp Server Setup Script
# Quick setup for CPU-only deployment

set -e

echo "========================================"
echo "llama.cpp Server Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Please run this script from the serverhost directory${NC}"
    exit 1
fi

echo "Step 1: Creating directories..."
mkdir -p models upload-ui/templates

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo "Step 2: Checking for models..."
if [ ! -d "../finetunedmodels/qwen3-1.7b-trading-q4km" ]; then
    echo -e "${YELLOW}⚠ Fine-tuned model not found in ../finetunedmodels/${NC}"
    echo "Please ensure you have completed the training and model export."
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Found fine-tuned model${NC}"
    
    # Copy model if not already present
    if [ ! -f "models/qwen3-trading.gguf" ]; then
        echo "Copying model to serverhost/models/..."
        cp ../finetunedmodels/qwen3-1.7b-trading-q4km/qwen3-1.7b-trading-Q4_K_M.gguf \
           models/qwen3-trading.gguf
        echo -e "${GREEN}✓ Model copied${NC}"
    else
        echo -e "${YELLOW}⚠ Model already exists, skipping copy${NC}"
    fi
    
    # Create symlink to active model
    echo "Setting as active model..."
    cd models
    ln -sf qwen3-trading.gguf current.gguf
    cd ..
    echo -e "${GREEN}✓ Active model set${NC}"
fi

echo ""
echo "Step 3: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not available${NC}"
    echo "Please install Docker Compose or update Docker Desktop"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo ""

echo "Step 4: Building and starting services..."
docker compose up -d --build

echo ""
echo "Step 5: Waiting for services to start..."
sleep 5

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Services are running${NC}"
else
    echo -e "${RED}✗ Services failed to start${NC}"
    echo "Check logs with: docker compose logs"
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "📤 Upload UI:       http://localhost:3000"
echo "🚀 llama.cpp WebUI: http://localhost:8080"
echo ""
echo "Useful commands:"
echo "  docker compose logs -f        # View logs"
echo "  docker compose restart        # Restart services"
echo "  docker compose down           # Stop services"
echo "  docker compose ps             # Check status"
echo ""
echo "View the README.md for detailed documentation"
echo ""

# Try to open browser (optional)
if command -v open &> /dev/null; then
    read -p "Open Upload UI in browser? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:3000
    fi
fi

echo "Happy chatting! 🦙"

