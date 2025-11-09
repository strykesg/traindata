#!/bin/bash
# Quick version check script

echo "=========================================="
echo "Package Versions"
echo "=========================================="
echo ""

python3 -c "
import sys
print(f'Python: {sys.version.split()[0]}')

try:
    import torch
    print(f'PyTorch: {torch.__version__}')
    print(f'CUDA Available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'CUDA Version: {torch.version.cuda}')
        print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'torch.int1 exists: {hasattr(torch, \"int1\")}')
except ImportError:
    print('PyTorch: NOT INSTALLED')

try:
    import transformers
    print(f'transformers: {transformers.__version__}')
except ImportError:
    print('transformers: NOT INSTALLED')

try:
    import unsloth
    print('unsloth: INSTALLED')
except ImportError:
    print('unsloth: NOT INSTALLED')

try:
    import accelerate
    print(f'accelerate: {accelerate.__version__}')
except ImportError:
    print('accelerate: NOT INSTALLED')

try:
    import bitsandbytes
    print(f'bitsandbytes: {bitsandbytes.__version__}')
except ImportError:
    print('bitsandbytes: NOT INSTALLED')

try:
    import peft
    print(f'peft: {peft.__version__}')
except ImportError:
    print('peft: NOT INSTALLED')

try:
    import trl
    print(f'trl: {trl.__version__}')
except ImportError:
    print('trl: NOT INSTALLED')
"

echo ""
echo "=========================================="

