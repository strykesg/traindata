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

# Find and comment out all problematic torch.int* lines
lines = content.split('\n')
patched_types = []
for i, line in enumerate(lines):
    # Check for torch.int1, int2, int4, etc. that might not be available
    for int_type in ['int1', 'int2', 'int4']:
        if f'torch.{int_type}:' in line and '#' not in line.split(f'torch.{int_type}:')[0]:
            # Comment out this line
            indent = len(line) - len(line.lstrip())
            # Extract the value part if present
            if ':' in line:
                value_part = line.split(':', 1)[1].strip()
                lines[i] = f'{" " * indent}# torch.{int_type}: {value_part}  # Patched: not available in all PyTorch builds'
            else:
                lines[i] = f'{" " * indent}# torch.{int_type}: ...  # Patched: not available in all PyTorch builds'
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

