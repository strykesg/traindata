#!/bin/bash
# Direct fix for torchao's quant_primitives.py file

echo "=========================================="
echo "Fixing torchao quant_primitives.py directly"
echo "=========================================="

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Find torchao installation without importing it (since import fails)
# Try multiple methods to find the path
TORCHAO_PATH=""

# Method 1: Try to find via pip show
TORCHAO_PATH=$(pip show torchao 2>/dev/null | grep "Location:" | awk '{print $2}')
if [ -n "$TORCHAO_PATH" ]; then
    TORCHAO_PATH="$TORCHAO_PATH/torchao"
fi

# Method 2: Try common site-packages locations
if [ ! -d "$TORCHAO_PATH" ] || [ -z "$TORCHAO_PATH" ]; then
    # Find venv or site-packages
    if [ -d "venv" ]; then
        TORCHAO_PATH="venv/lib/python$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages/torchao"
    else
        # Try system site-packages
        TORCHAO_PATH=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)/torchao
    fi
fi

# Method 3: Search for it
if [ ! -d "$TORCHAO_PATH" ] || [ -z "$TORCHAO_PATH" ]; then
    TORCHAO_PATH=$(find . -type d -name "torchao" -path "*/site-packages/torchao" 2>/dev/null | head -1)
fi

if [ -z "$TORCHAO_PATH" ] || [ ! -d "$TORCHAO_PATH" ]; then
    echo "ERROR: Could not find torchao installation"
    echo "Tried: $TORCHAO_PATH"
    echo "Please specify the path manually or ensure torchao is installed"
    echo ""
    echo "To find it manually, run:"
    echo "  find . -name 'torchao' -type d"
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

# Find and comment out ALL problematic torch.int* lines (int1, int2, int3, int4)
lines = content.split('\n')
patched_types = []
for i, line in enumerate(lines):
    # Check for any torch.int* lines that aren't already commented
    if 'torch.int' in line and ':' in line and not line.strip().startswith('#'):
        # Check if it's int1, int2, int3, or int4
        for int_type in ['int1', 'int2', 'int3', 'int4']:
            if f'torch.{int_type}:' in line:
                # Comment out this line
                indent = len(line) - len(line.lstrip())
                # Extract the value part if present
                if ':' in line:
                    value_part = line.split(':', 1)[1].strip()
                    lines[i] = f'{" " * indent}# torch.{int_type}: {value_part}  # Patched: not available in all PyTorch builds'
                else:
                    lines[i] = f'{" " * indent}# torch.{int_type}: ...  # Patched: not available in all PyTorch builds'
                if int_type not in patched_types:
                    patched_types.append(int_type)
                break

if patched_types:
    content = '\n'.join(lines)
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Successfully patched quant_primitives.py")
    print(f"Commented out: {', '.join(f'torch.{t}' for t in patched_types)}")
else:
    print("Warning: No torch.int* lines found to patch (may already be patched)")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "Patch complete! Try running train.py again."
echo "To restore original: cp $QUANT_PRIMITIVES.backup $QUANT_PRIMITIVES"
echo "=========================================="

