#!/usr/bin/env python3
"""
Environment check script for Unsloth training.
Verifies all requirements are met before training.
"""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (need 3.10+)")
        return False

def check_torch():
    """Check PyTorch installation and torch.int1 support."""
    print("\n🔍 Checking PyTorch...")
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        
        # Check CUDA
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   Number of GPUs: {torch.cuda.device_count()}")
        else:
            print("⚠️  CUDA not available")
        
        # Check for torch.int1 (critical for torchao)
        if hasattr(torch, 'int1'):
            print("✅ torch.int1 supported (torchao compatible)")
        else:
            print("❌ torch.int1 NOT supported")
            print("   -> You need PyTorch 2.5.1+")
            print("   -> Run: bash fix_torch.sh or python fix_torchao.py")
            return False
        
        # Check torchvision compatibility
        try:
            import torchvision
            print(f"✅ torchvision {torchvision.__version__}")
            
            # Test if torchvision works with this PyTorch version
            try:
                from torchvision.transforms import InterpolationMode
                print("✅ torchvision compatible with PyTorch")
            except Exception as e:
                print(f"❌ torchvision NOT compatible: {e}")
                print("   -> Run: bash fix_torchvision.sh")
                return False
        except ImportError:
            print("⚠️  torchvision not installed")
        
        return True
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def check_transformers():
    """Check transformers installation."""
    print("\n🔍 Checking transformers...")
    try:
        import transformers
        print(f"✅ transformers {transformers.__version__}")
        return True
    except ImportError:
        print("❌ transformers not installed")
        return False

def check_unsloth():
    """Check unsloth installation."""
    print("\n🔍 Checking unsloth...")
    try:
        import unsloth
        print(f"✅ unsloth installed")
        from unsloth import FastLanguageModel
        print("✅ FastLanguageModel importable")
        return True
    except ImportError as e:
        print(f"❌ unsloth not installed or import error: {e}")
        return False

def check_other_dependencies():
    """Check other critical dependencies."""
    print("\n🔍 Checking other dependencies...")
    dependencies = {
        'accelerate': 'accelerate',
        'bitsandbytes': 'bitsandbytes',
        'peft': 'peft',
        'trl': 'trl',
        'datasets': 'datasets',
        'wandb': 'wandb',
    }
    
    all_ok = True
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_ok = False
    
    return all_ok

def check_data_directory():
    """Check if data directory exists with required files."""
    print("\n🔍 Checking data directory...")
    data_dir = Path("data")
    
    if not data_dir.exists():
        print("❌ data/ directory not found")
        return False
    
    print("✅ data/ directory exists")
    
    train_file = data_dir / "train.jsonl"
    if train_file.exists():
        print(f"✅ train.jsonl found ({train_file.stat().st_size / 1024:.1f} KB)")
    else:
        print("❌ train.jsonl not found")
        return False
    
    val_file = data_dir / "val.jsonl"
    if val_file.exists():
        print(f"✅ val.jsonl found ({val_file.stat().st_size / 1024:.1f} KB)")
    else:
        print("⚠️  val.jsonl not found (optional)")
    
    return True

def check_env_variables():
    """Check environment variables."""
    print("\n🔍 Checking environment variables...")
    import os
    
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print("✅ HF_TOKEN is set")
    else:
        print("⚠️  HF_TOKEN not set (needed for downloading models)")
    
    wandb_key = os.getenv("WANDB_API_KEY")
    if wandb_key:
        print("✅ WANDB_API_KEY is set")
    else:
        print("⚠️  WANDB_API_KEY not set (logging will be disabled)")
    
    return True

def main():
    """Run all checks."""
    print("=" * 60)
    print("Unsloth Training Environment Check")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_torch(),
        check_transformers(),
        check_unsloth(),
        check_other_dependencies(),
        check_data_directory(),
        check_env_variables(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks[:5]):  # Critical checks (excluding data and env vars)
        print("✅ Environment is ready for training!")
        if not checks[5]:
            print("⚠️  But you need to add training data first")
        if not all(checks[6:]):
            print("⚠️  Some environment variables are missing")
        print("\nYou can now run:")
        print("  python train.py")
    else:
        print("❌ Environment has issues that need to be fixed")
        print("\nPlease fix the errors above before training.")
        if not hasattr(__import__('torch'), 'int1'):
            print("\n💡 Quick fix for torch.int1 error:")
            print("   bash fix_torch.sh")
    print("=" * 60)

if __name__ == "__main__":
    main()

