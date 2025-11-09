#!/usr/bin/env python3
"""
Simple script to patch torchao's quant_primitives.py to handle missing torch.int* types.
Run this before importing unsloth.
"""
import os
import sys

# Find torchao path
try:
    import site
    site_packages = site.getsitepackages()
    
    torchao_path = None
    for sp in site_packages:
        candidate = os.path.join(sp, 'torchao')
        if os.path.exists(candidate):
            torchao_path = candidate
            break
    
    # Also check venv
    if not torchao_path:
        venv_path = os.path.join(os.getcwd(), 'venv', 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages', 'torchao')
        if os.path.exists(venv_path):
            torchao_path = venv_path
    
    if not torchao_path:
        print("ERROR: Could not find torchao installation")
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
    
    # Read and patch
    with open(quant_primitives, 'r') as f:
        lines = f.readlines()
    
    patched = False
    for i, line in enumerate(lines):
        # Comment out any torch.int* lines that aren't already commented
        if 'torch.int' in line and ':' in line and not line.strip().startswith('#'):
            # Check if it's a dictionary entry line
            if any(f'torch.int{x}:' in line for x in [1, 2, 3, 4]):
                indent = len(line) - len(line.lstrip())
                lines[i] = ' ' * indent + '# ' + line.lstrip()
                patched = True
    
    if patched:
        with open(quant_primitives, 'w') as f:
            f.writelines(lines)
        print("SUCCESS: Patched quant_primitives.py - commented out all torch.int* lines")
        print("You can now run: python train.py")
    else:
        print("No changes needed (may already be patched)")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

