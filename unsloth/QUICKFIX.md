# Quick Fix for torch.int1 Error on A100

## The Problem

You're seeing this error:
```
AttributeError: module 'torch' has no attribute 'int1'
```

This happens because `torchao` (a dependency of newer transformers) requires PyTorch 2.5.1+ which supports `torch.int1`, but your environment has an older version.

## The Solution (5 minutes)

On your vast.ai instance, run these commands:

```bash
# Make sure you're in the unsloth directory
cd /workspace/traindata/unsloth

# Activate your virtual environment
source venv/bin/activate

# Load environment variables
source .env

# Run the fix script
bash fix_torch.sh
```

That's it! The script will:
1. Uninstall old PyTorch
2. Install PyTorch 2.5.1 with CUDA 12.1
3. Reinstall unsloth and dependencies
4. Verify everything works

## Alternative: CUDA 12.4

If you need CUDA 12.4 instead:

```bash
bash fix_torch_cu124.sh
```

## Verify the Fix

After running the fix, check your environment:

```bash
python check_env.py
```

You should see:
- ✅ PyTorch 2.5.1
- ✅ CUDA available: NVIDIA A100-SXM4-40GB (or similar)
- ✅ torch.int1 supported (torchao compatible)

## Start Training

Once the check passes:

```bash
python train.py
```

## Manual Fix (if scripts don't work)

```bash
# Uninstall old PyTorch
pip uninstall -y torch torchvision torchaudio

# Install PyTorch 2.5.1 with CUDA 12.1
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Force reinstall unsloth
pip install --upgrade --force-reinstall --no-deps unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git

# Reinstall dependencies
pip install transformers>=4.51.0 accelerate bitsandbytes peft trl datasets

# Verify
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'torch.int1: {hasattr(torch, \"int1\")}')"
```

## Why This Happened

The `unsloth[colab-new]` package installs the latest transformers, which includes `torchao` for quantization optimizations. Recent versions of `torchao` use `torch.int1`, a data type introduced in PyTorch 2.5.0.

Your original setup installed an older PyTorch version that doesn't have this feature, causing the error.

## Prevention for Fresh Installs

For future setups, use the updated `setup_vast.sh` script which now installs PyTorch 2.5.1 first:

```bash
bash setup_vast.sh
```

This ensures compatible versions from the start.

