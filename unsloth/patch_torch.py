"""
Patch script to fix torch.int1 compatibility issue.
Run this before importing unsloth if torch.int1 is not available.
"""
import torch

if not hasattr(torch, 'int1'):
    print("Warning: torch.int1 not available, creating workaround...")
    # Create a placeholder int1 dtype
    # torchao uses this for quantization, but we can work around it
    torch.int1 = type('int1', (), {
        '__repr__': lambda self: "torch.int1",
        '__str__': lambda self: "torch.int1",
    })()
    print("Workaround applied: torch.int1 placeholder created")

