"""
Direct patch for torchao's quant_primitives.py to handle missing torch.int1.
This patches the file directly before import.
"""
import os
import sys
import torch

# Find torchao installation
try:
    import torchao
    torchao_path = os.path.dirname(torchao.__file__)
except ImportError:
    # Try to find it manually
    import site
    for site_package in site.getsitepackages():
        torchao_path = os.path.join(site_package, 'torchao')
        if os.path.exists(torchao_path):
            break
    else:
        print("Warning: Could not find torchao installation")
        torchao_path = None

if torchao_path and not hasattr(torch, 'int1'):
    quant_primitives_path = os.path.join(torchao_path, 'quantization', 'quant_primitives.py')
    
    if os.path.exists(quant_primitives_path):
        print("Patching torchao's quant_primitives.py directly...")
        
        # Read the file
        with open(quant_primitives_path, 'r') as f:
            content = f.read()
        
        # Patch the problematic line
        # Replace: torch.int1: (-(2**0), 2**0 - 1),
        # With a try/except or comment it out
        if 'torch.int1:' in content and 'try:' not in content.split('torch.int1:')[0][-200:]:
            # Add try/except around the dictionary
            content = content.replace(
                'torch.int1: (-(2**0), 2**0 - 1),',
                '# torch.int1: (-(2**0), 2**0 - 1),  # Patched: not available in all PyTorch builds'
            )
            
            # Write back
            with open(quant_primitives_path, 'w') as f:
                f.write(content)
            
            print("Successfully patched torchao's quant_primitives.py")
        else:
            print("torchao already patched or structure changed")

