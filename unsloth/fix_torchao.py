#!/usr/bin/env python3
"""
Fix torchao compatibility with PyTorch builds that don't have torch.int1/int2/etc.
This patches the torchao quant_primitives.py file to handle missing int types gracefully.
"""
import sys
import os
import re

def find_torchao_file():
    """Find the torchao quant_primitives.py file."""
    try:
        import torchao
        torchao_path = os.path.dirname(torchao.__file__)
        target_file = os.path.join(torchao_path, 'quantization', 'quant_primitives.py')
        if os.path.exists(target_file):
            return target_file
    except ImportError:
        pass
    
    # Try common venv locations
    for base in ['venv', '.venv', 'env']:
        for version in ['3.12', '3.11', '3.10', '3.9']:
            path = f"{base}/lib/python{version}/site-packages/torchao/quantization/quant_primitives.py"
            if os.path.exists(path):
                return path
    
    return None

def patch_file(filepath):
    """Patch the torchao file to handle missing int types."""
    print(f"Patching {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'PATCHED FOR COMPATIBILITY' in content:
        print("✓ File already patched")
        return True
    
    # Find the DTYPE_RANGE_MAP section and patch it
    pattern = r'(DTYPE_RANGE_MAP\s*=\s*{[^}]*)(torch\.int\d+:[^,]+,?\s*)+'
    
    # New safe implementation
    replacement = r'''DTYPE_RANGE_MAP = {
    # PATCHED FOR COMPATIBILITY - handles missing torch.int types
    **{
        torch.uint8: (0, 2**8 - 1),
        torch.int8: (-(2**7), 2**7 - 1),
        torch.int16: (-(2**15), 2**15 - 1),
        torch.int32: (-(2**31), 2**31 - 1),
        torch.int64: (-(2**63), 2**63 - 1),
    },
    # Add int1-8 only if they exist in this PyTorch build
    **{getattr(torch, f'int{i}'): (-(2**(i-1)), 2**(i-1) - 1) 
       for i in range(1, 9) if hasattr(torch, f'int{i}')},
'''
    
    # Try to replace
    if 'DTYPE_RANGE_MAP' in content:
        # More aggressive approach: replace the entire problematic section
        lines = content.split('\n')
        new_lines = []
        skip_until_closing = False
        brace_count = 0
        
        for i, line in enumerate(lines):
            if 'DTYPE_RANGE_MAP' in line and not skip_until_closing:
                # Found start of DTYPE_RANGE_MAP
                new_lines.append(replacement)
                skip_until_closing = True
                brace_count = line.count('{') - line.count('}')
                continue
            
            if skip_until_closing:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and '}' in line:
                    # Found closing brace
                    new_lines.append('}')
                    skip_until_closing = False
                continue
            
            new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        print("✓ Successfully patched torchao file")
        return True
    else:
        print("✗ Could not find DTYPE_RANGE_MAP in file")
        return False

def main():
    """Main entry point."""
    print("=" * 60)
    print("torchao PyTorch Compatibility Patcher")
    print("=" * 60)
    print()
    
    # Find the file
    filepath = find_torchao_file()
    if not filepath:
        print("✗ Could not find torchao installation")
        print("Make sure torchao is installed: pip install torchao")
        return 1
    
    print(f"Found torchao at: {filepath}")
    print()
    
    # Patch it
    try:
        success = patch_file(filepath)
        if success:
            print()
            print("=" * 60)
            print("✓ Patch applied successfully!")
            print("You can now run: python train.py")
            print("=" * 60)
            return 0
        else:
            print()
            print("✗ Patching failed")
            return 1
    except Exception as e:
        print(f"✗ Error patching file: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

