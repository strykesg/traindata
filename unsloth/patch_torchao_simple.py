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
        content = f.read()
    
    # Find the dictionary that contains torch.int* entries
    # Look for the pattern where torch.int* is used in a dictionary
    # We'll wrap it in a try/except or comment out all torch.int* lines
    
    lines = content.split('\n')
    patched = False
    
    # Find the dictionary block (usually starts with something like "DTYPE_TO_RANGE = {")
    dict_start = -1
    dict_end = -1
    in_dict = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        # Look for dictionary definition
        if 'DTYPE_TO_RANGE' in line or 'dtype_to_range' in line or ('{' in line and 'torch.int' in content[max(0, i-5):i+5]):
            if '{' in line:
                dict_start = i
                in_dict = True
                # Count opening braces to find end
                brace_count = line.count('{') - line.count('}')
                indent_level = len(line) - len(line.lstrip())
                continue
        
        if in_dict:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '}' in line:
                dict_end = i
                break
    
    # If we found a dictionary, patch all torch.int* lines in it
    if dict_start >= 0:
        for i in range(dict_start, min(dict_end + 1 if dict_end >= 0 else len(lines), len(lines))):
            line = lines[i]
            # Comment out any torch.int* lines (int1, int2, int3, int4, int5, etc.)
            if 'torch.int' in line and ':' in line and not line.strip().startswith('#'):
                # Check if it matches pattern torch.int<digit>:
                import re
                if re.search(r'torch\.int\d+:', line):
                    indent = len(line) - len(line.lstrip())
                    lines[i] = ' ' * indent + '# ' + line.lstrip() + '  # Patched: not available in all PyTorch builds'
                    patched = True
    else:
        # Fallback: just comment out all torch.int* lines
        for i, line in enumerate(lines):
            if 'torch.int' in line and ':' in line and not line.strip().startswith('#'):
                import re
                if re.search(r'torch\.int\d+:', line):
                    indent = len(line) - len(line.lstrip())
                    lines[i] = ' ' * indent + '# ' + line.lstrip() + '  # Patched: not available in all PyTorch builds'
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

