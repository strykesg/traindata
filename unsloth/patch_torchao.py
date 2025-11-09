"""
Pre-import patch for torchao to handle missing torch.int1.
This must be imported BEFORE unsloth to work.
"""
import torch
import sys

# Patch torch.int1 before torchao imports
if not hasattr(torch, 'int1'):
    print("Patching torch.int1 for torchao compatibility...")
    
    class Int1DType:
        """Placeholder for torch.int1 dtype."""
        def __repr__(self):
            return "torch.int1"
        def __str__(self):
            return "torch.int1"
        def __hash__(self):
            return hash("torch.int1")
        def __eq__(self, other):
            return isinstance(other, Int1DType) or str(other) == "torch.int1"
    
    torch.int1 = Int1DType()
    sys.modules['torch'].int1 = torch.int1
    
    print("torch.int1 patch applied successfully")

