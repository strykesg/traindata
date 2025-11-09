#!/usr/bin/env python3
"""
Complete fix: Patch torchao's quant_primitives.py to comment out ALL torch.int* lines.
This handles int1, int2, int3, int4, int5, etc. - any missing int type.
"""
import os
import sys
import re

def find_torchao():
    """Find torchao installation path."""
    # Try venv first
    if os.path.exists('venv'):
        import sys
        venv_path = f'venv/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/torchao'
        if os.path.exists(venv_path):
            return venv_path
    
    # Try site-packages
    import site
    for sp in site.getsitepackages():
        candidate = os.path.join(sp, 'torchao')
        if os.path.exists(candidate):
            return candidate
    
    return None

def main():
    torchao_path = find_torchao()
    
    if not torchao_path:
        print("ERROR: Could not find torchao installation")
        print("Make sure you're in the unsloth directory and torchao is installed")
        sys.exit(1)
    
    quant_primitives = os.path.join(torchao_path, 'quantization', 'quant_primitives.py')
    
    if not os.path.exists(quant_primitives):
        print(f"ERROR: Could not find {quant_primitives}")
        sys.exit(1)
    
    print(f"Found torchao at: {torchao_path}")
    print(f"Patching: {quant_primitives}")
    
    # Backup
    backup_path = quant_primitives + '.backup'
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy(quant_primitives, backup_path)
        print(f"Backup created: {backup_path}")
    else:
        print(f"Backup already exists: {backup_path}")
    
    # Read file
    with open(quant_primitives, 'r') as f:
        lines = f.readlines()
    
    # Patch: comment out ALL torch.int* lines (int1, int2, int3, int4, int5, etc.)
    patched_count = 0
    for i, line in enumerate(lines):
        # Match pattern: torch.int<digits>: (any number of digits)
        if re.search(r'torch\.int\d+:', line) and not line.strip().startswith('#'):
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + '# ' + line.lstrip() + '  # Patched: not available in all PyTorch builds\n'
            patched_count += 1
    
    if patched_count > 0:
        # Write back
        with open(quant_primitives, 'w') as f:
            f.writelines(lines)
        print(f"SUCCESS: Commented out {patched_count} torch.int* lines")
        print("You can now run: python train.py")
    else:
        print("No torch.int* lines found to patch (may already be patched)")

if __name__ == '__main__':
    main()

