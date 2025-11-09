## Post-Training Workflow Guide

Complete guide for exporting, quantizing, and downloading your fine-tuned model after training completes.

## 📋 Overview

After training completes, you need to:
1. **Export** the model from the training format
2. **Quantize** to GGUF Q4_K_M for efficient inference
3. **Download** to your local machine

## 🚀 Quick Start (Automated)

### On Training Server:
```bash
# Run the complete workflow (after training finishes)
bash complete_workflow.sh
```

### On Your Local Machine:
```bash
# Download the model
bash download_model.sh

# Check training status anytime
bash check_training.sh
```

---

## 📖 Detailed Workflow

### 1. Monitor Training

**From your local machine:**
```bash
# Check if training is running and view status
bash check_training.sh

# Or watch logs in real-time
ssh -p 32613 root@157.90.56.162 'tail -f /workspace/traindata/unsloth/training_balanced.log'
```

### 2. After Training Completes

**On the training server (SSH in):**

#### Option A: Automated (Recommended)
```bash
ssh -p 32613 root@157.90.56.162
cd /workspace/traindata/unsloth
bash complete_workflow.sh
```

This runs everything automatically:
- Exports the model
- Quantizes to GGUF Q4_K_M
- Prepares for download

#### Option B: Manual Steps

**Step 2.1: Export the model**
```bash
python export_and_quantize.py
```

Creates:
- `finetunedmodels/qwen3-1.7b-trading-bot-TIMESTAMP/`
  - Full model files (safetensors, config, tokenizer)
  - Model card (MODEL_CARD.md)
  - Metadata (metadata.json)

**Step 2.2: Quantize to GGUF**
```bash
bash quantize_to_gguf.sh
```

Creates:
- `*-FP16.gguf` - Full precision GGUF (~3.4GB)
- `*-Q4_K_M.gguf` - 4-bit quantized GGUF (~1.1GB)
- `QUANTIZATION_INFO.md` - Usage guide

### 3. Download to Local Machine

**On your local machine:**
```bash
# Interactive download with options
bash download_model.sh
```

**Download options:**
1. **Full model + Q4_K_M** (recommended) - ~4GB
   - Can use with transformers or llama.cpp
   
2. **Q4_K_M only** (smallest) - ~1.1GB
   - Fastest download, llama.cpp only
   
3. **Full model only** - ~3.4GB
   - Transformers only
   
4. **Everything** - ~5GB
   - All formats for maximum flexibility

---

## 📁 Output Structure

After completion, you'll have:

```
finetunedmodels/
└── qwen3-1.7b-trading-bot-20251109_123456/
    ├── model-00001-of-00002.safetensors    # Full model weights
    ├── model-00002-of-00002.safetensors
    ├── model.safetensors.index.json
    ├── config.json                         # Model configuration
    ├── tokenizer.json                      # Tokenizer
    ├── tokenizer_config.json
    ├── special_tokens_map.json
    ├── qwen3-1.7b-trading-bot-...-FP16.gguf       # Full GGUF
    ├── qwen3-1.7b-trading-bot-...-Q4_K_M.gguf     # Quantized GGUF ⭐
    ├── MODEL_CARD.md                       # Documentation
    ├── QUANTIZATION_INFO.md                # GGUF usage guide
    └── metadata.json                       # Training metadata
```

---

## 🎯 Using the Models

### Option 1: Quantized GGUF (Recommended)

**With llama.cpp:**
```bash
./llama-cli -m qwen3-1.7b-trading-bot-...-Q4_K_M.gguf \
    -p "Market analysis for BTC..." \
    -n 512 \
    --temp 0.7
```

**With llama-cpp-python:**
```python
from llama_cpp import Llama

llm = Llama(
    model_path="qwen3-1.7b-trading-bot-...-Q4_K_M.gguf",
    n_ctx=2048,
    n_gpu_layers=-1  # Use GPU if available
)

output = llm(
    "Market analysis for BTC...",
    max_tokens=512,
    temperature=0.7
)
print(output['choices'][0]['text'])
```

### Option 2: Full Model with Transformers

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "./downloaded_models/qwen3-1.7b-trading-bot-...",
    device_map="auto",
    torch_dtype="auto"
)
tokenizer = AutoTokenizer.from_pretrained(
    "./downloaded_models/qwen3-1.7b-trading-bot-..."
)

messages = [
    {"role": "system", "content": "You are Dexter, a crypto trading assistant."},
    {"role": "user", "content": "Market analysis for BTC..."}
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.7)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

---

## 📊 File Sizes Reference

| Format | Size | Speed | Quality | Use Case |
|--------|------|-------|---------|----------|
| Full Model (safetensors) | ~3.4GB | Baseline | 100% | Training, high-end inference |
| FP16 GGUF | ~3.4GB | Fast | 100% | CPU/GPU inference |
| **Q4_K_M GGUF** | **~1.1GB** | **Very Fast** | **~99%** | **Production (recommended)** |

---

## ⚠️ Troubleshooting

### Training not complete?
```bash
# Check status
bash check_training.sh

# View live logs
ssh -p 32613 root@157.90.56.162 'tail -f /workspace/traindata/unsloth/training*.log'
```

### Export failed?
```bash
# Check if training output exists
ssh -p 32613 root@157.90.56.162 'ls -la /workspace/traindata/unsloth/output_model/'

# Re-run export
ssh -p 32613 root@157.90.56.162 'cd /workspace/traindata/unsloth && python export_and_quantize.py'
```

### Quantization failed?
```bash
# Make sure llama.cpp is installed
ssh -p 32613 root@157.90.56.162 'cd /workspace/traindata/unsloth && bash quantize_to_gguf.sh'

# Or install llama.cpp manually
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make -j$(nproc)
```

### Download interrupted?
```bash
# Rsync will resume from where it stopped
bash download_model.sh
# Select same option to resume
```

---

## 🎓 Tips

1. **Q4_K_M is optimal**: Best balance of size/quality/speed for production
2. **Keep FP16 GGUF**: Useful for later re-quantization to other formats
3. **Test locally first**: Run quick inference tests before deploying
4. **Save training logs**: Keep logs for reference and debugging
5. **Document everything**: MODEL_CARD.md contains important training details

---

## 🔗 Related Scripts

- **check_training.sh** - Monitor training status
- **export_and_quantize.py** - Export model from training format
- **quantize_to_gguf.sh** - Convert to GGUF and quantize
- **download_model.sh** - Download from server to local
- **complete_workflow.sh** - Run all steps automatically

---

## 📞 Quick Reference

```bash
# Check training
bash check_training.sh

# After training (on server)
bash complete_workflow.sh

# Download (on local)
bash download_model.sh

# Test model
python downloaded_models/qwen3-1.7b-trading-bot-*/test_model.py
```

---

Generated: 2025-11-09

