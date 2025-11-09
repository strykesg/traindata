# Qwen3-1.7B Fine-tuning with Unsloth

Fine-tune Qwen3-1.7B on vast.ai GTX 5090 using Unsloth for efficient training.

## Setup

### 1. Environment Variables

Create a `.env` file or set environment variables:

```bash
# HuggingFace
export HF_TOKEN="your_huggingface_token"
export HF_USERNAME="your_username"
export HF_MODEL_ID="your-username/qwen3-1.7b-trading-bot"  # Optional, defaults to username/qwen3-1.7b-trading-bot

# WandB
export WANDB_API_KEY="your_wandb_api_key"
export WANDB_PROJECT="qwen3-1.7b-finetune"  # Optional, defaults to this

# Data directory (relative to script location)
export DATA_DIR="data"  # Default is "data" directory, change if needed
```

### 2. Install Dependencies

**Important:** PyTorch 2.5.1+ is required for `torch.int1` support (needed by torchao).

```bash
# Install PyTorch 2.5.1 with CUDA 12.1 first
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Then install other dependencies
pip install -r requirements.txt
```

**For automated setup on vast.ai:**
```bash
bash setup_vast.sh  # Interactive setup with environment variables
```

### 3. Prepare Training Data

Place your training data in the `data/` directory:
- `data/train.jsonl` - Training examples
- `data/val.jsonl` - Validation examples (optional)
- `data/test.jsonl` - Test examples (not used in training)

**Quick setup:** After generating data with the main script:
```bash
cp output/train.jsonl unsloth/data/
cp output/val.jsonl unsloth/data/
cp output/test.jsonl unsloth/data/
```

Each line should be a JSON object with the LLaMA chat template format:
```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

### 4. Run Training

```bash
python train.py
```

## Configuration

Edit `train.py` to adjust:

- **MODEL_NAME**: Model to fine-tune (default: `Qwen/Qwen3-1.7B`)
- **MAX_SEQ_LENGTH**: Maximum sequence length (default: 2048)
- **BATCH_SIZE**: Per-device batch size (default: 4, adjust for GPU memory)
- **GRADIENT_ACCUMULATION_STEPS**: Gradient accumulation (default: 4)
- **NUM_EPOCHS**: Number of training epochs (default: 3)
- **LEARNING_RATE**: Learning rate (default: 2e-4)
- **LoRA rank**: `r=16` in `get_peft_model()` (increase for more capacity)

## vast.ai Deployment

### 1. Create Instance

- Select GTX 5090 (or similar high-memory GPU)
- Use Ubuntu 22.04 or similar
- Ensure sufficient disk space (50GB+ recommended)

### 2. Setup Script

```bash
# On vast.ai instance
git clone <your-repo-url>
cd finetuningscript/unsloth

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export HF_TOKEN="your_token"
export WANDB_API_KEY="your_key"
# DATA_DIR defaults to "data" directory, no need to set if using default

# Run training
python train.py
```

### 3. Monitor Training

- WandB dashboard: https://wandb.ai
- Check logs for progress
- Model checkpoints saved to `output_model/` directory

## Expected Performance

On GTX 5090 (24GB VRAM):
- **Batch size**: 4-8 (depending on sequence length)
- **Training speed**: ~2-5 examples/second
- **Time for 23K examples**: ~1-3 hours per epoch
- **Total time (3 epochs)**: ~3-9 hours

## Model Output

After training:
- Model saved to `output_model/` directory
- Optionally pushed to HuggingFace Hub (if `HF_TOKEN` and `HF_MODEL_ID` set)
- WandB logs contain training metrics

## Usage After Fine-tuning

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("output_model")
tokenizer = AutoTokenizer.from_pretrained("output_model")

# Use the fine-tuned model
messages = [
    {"role": "user", "content": "Market context: {...}\n\nWhat should we do?"}
]
text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## Troubleshooting

### AttributeError: module 'torch' has no attribute 'int1'

This error occurs when PyTorch version is too old for the `torchao` dependency. 

**Quick Fix:**
```bash
# Activate your venv if not already active
source venv/bin/activate

# Run the fix script (CUDA 12.1)
bash fix_torch.sh

# Or for CUDA 12.4
bash fix_torch_cu124.sh
```

**Manual Fix:**
```bash
# Uninstall old PyTorch
pip uninstall -y torch torchvision torchaudio

# Install PyTorch 2.5.1 with CUDA 12.1
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Or for CUDA 12.4
pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Reinstall unsloth
pip install --upgrade --force-reinstall unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git
```

### Out of Memory
- Reduce `BATCH_SIZE`
- Increase `GRADIENT_ACCUMULATION_STEPS`
- Reduce `MAX_SEQ_LENGTH`
- Use `load_in_4bit=True` (already enabled)

### Slow Training
- Increase `BATCH_SIZE` if memory allows
- Set `packing=True` in SFTTrainer if sequences are short
- Use bfloat16 if GPU supports it (auto-detected)

### WandB Issues
- Verify `WANDB_API_KEY` is set
- Check internet connection
- Set `report_to="none"` to disable WandB if needed

