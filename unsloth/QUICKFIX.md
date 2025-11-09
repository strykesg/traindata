# Quick Fix for torch.int1 Error

## The Problem

```
AttributeError: module 'torch' has no attribute 'int1'
```

This happens because `torchao` expects certain int types (`torch.int1`, `torch.int2`, etc.) that don't exist in some PyTorch builds, especially CUDA-enabled builds.

## The Solution

### On your vast.ai instance, run:

```bash
cd /workspace/traindata/unsloth  # or wherever you cloned the repo
source venv/bin/activate
python fix_torchao.py
```

**That's it!** The script will:
1. Find your torchao installation
2. Patch the problematic file to handle missing int types
3. Confirm success

### Then run training normally:

```bash
python train.py
```

Or use the quickstart script (which now includes the fix):

```bash
bash quickstart.sh
```

## What the fix does

The `fix_torchao.py` script modifies `/path/to/torchao/quantization/quant_primitives.py` to:

1. Replace hardcoded `torch.int1`, `torch.int2`, etc. references
2. Use a dynamic dictionary that only includes int types that exist in your PyTorch build
3. Add a "PATCHED FOR COMPATIBILITY" marker (so it won't re-patch)

## Manual verification

After running the fix, test that it works:

```bash
python -c "import torchao; print('✓ torchao imports successfully')"
python -c "from unsloth import FastLanguageModel; print('✓ unsloth imports successfully')"
```

If both commands succeed without errors, you're ready to train!

## If the fix doesn't work

1. Make sure you're in the virtual environment:
   ```bash
   source venv/bin/activate
   which python  # Should show /workspace/.../venv/bin/python
   ```

2. Check torchao is installed:
   ```bash
   pip list | grep torchao
   ```

3. Try running with `sudo` if permissions are an issue:
   ```bash
   sudo python fix_torchao.py  # usually not needed
   ```

4. Check the fix was applied:
   ```bash
   grep "PATCHED FOR COMPATIBILITY" venv/lib/python*/site-packages/torchao/quantization/quant_primitives.py
   ```
   
   If this shows the line, the patch was applied.

## Alternative: Run setup again

The setup script now includes the fix automatically:

```bash
bash setup_vast.sh
```

This will re-run the entire setup and apply the fix at the end.
