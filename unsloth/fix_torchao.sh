#!/bin/bash
# Direct fix for torchao's quant_primitives.py file

echo "=========================================="
echo "Fixing torchao quant_primitives.py directly"
echo "=========================================="

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Find torchao installation
TORCHAO_PATH=$(python -c "import torchao; import os; print(os.path.dirname(torchao.__file__))" 2>/dev/null || echo "")

if [ -z "$TORCHAO_PATH" ]; then
    echo "ERROR: Could not find torchao installation"
    echo "Make sure torchao is installed: pip install torchao"
    exit 1
fi

QUANT_PRIMITIVES="$TORCHAO_PATH/quantization/quant_primitives.py"

if [ ! -f "$QUANT_PRIMITIVES" ]; then
    echo "ERROR: Could not find quant_primitives.py at $QUANT_PRIMITIVES"
    exit 1
fi

echo "Found torchao at: $TORCHAO_PATH"
echo "Patching: $QUANT_PRIMITIVES"

# Backup the file
cp "$QUANT_PRIMITIVES" "$QUANT_PRIMITIVES.backup"
echo "Backup created: $QUANT_PRIMITIVES.backup"

# Patch the file - comment out the problematic line
python3 << PYTHON_SCRIPT
import re
import sys

file_path = "$QUANT_PRIMITIVES"
with open(file_path, 'r') as f:
    content = f.read()

# Find and comment out the torch.int1 line
if 'torch.int1:' in content and '# torch.int1:' not in content:
    # Replace the problematic line - match various whitespace patterns
    lines = content.split('\n')
    patched = False
    for i, line in enumerate(lines):
        if 'torch.int1:' in line and '#' not in line.split('torch.int1:')[0]:
            # Comment out this line
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + '# torch.int1: (-(2**0), 2**0 - 1),  # Patched: not available in all PyTorch builds'
            patched = True
            break
    
    if patched:
        content = '\n'.join(lines)
        with open(file_path, 'w') as f:
            f.write(content)
        print("Successfully patched quant_primitives.py")
        print("The torch.int1 line has been commented out")
    else:
        print("Warning: Could not find uncommented torch.int1 line (may already be patched)")
else:
    print("Warning: torch.int1 line not found or already patched")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "Patch complete! Try running train.py again."
echo "To restore original: cp $QUANT_PRIMITIVES.backup $QUANT_PRIMITIVES"
echo "=========================================="

