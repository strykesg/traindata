# Fine-Tuning & Deployment Pipeline

Complete end-to-end solution for training, quantizing, and deploying custom AI models.

## 📁 Project Structure

```
finetuningscript/
│
├── unsloth/                        # Training environment
│   ├── train.py                    # Main training script
│   ├── create_balanced_dataset.py  # Dataset preparation
│   ├── data/                       # Training data (JSONL files)
│   ├── export_and_quantize.py      # Model export script
│   ├── merge_lora.py               # LoRA merging
│   └── POST_TRAINING.md            # Post-training guide
│
├── finetunedmodels/                # Exported models
│   └── qwen3-1.7b-trading-q4km/    # Your fine-tuned model
│       ├── qwen3-1.7b-trading-Q4_K_M.gguf  # Quantized model
│       ├── tokenizer files
│       └── README.md
│
└── serverhost/                     # Deployment setup
    ├── docker-compose.yml          # Service orchestration
    ├── setup.sh                    # Automated setup
    ├── models/                     # Model storage
    ├── upload-ui/                  # Model management UI
    ├── README.md                   # Deployment guide
    └── QUICKSTART.md               # Quick start
```

---

## 🎯 Three Main Components

### 1. Training (`unsloth/`)

**Purpose**: Fine-tune language models efficiently

**Key Features**:
- Unsloth for fast training
- LoRA for parameter-efficient fine-tuning
- Balanced dataset (trading + tools + reasoning)
- WandB integration for tracking

**Quick Start**:
```bash
cd unsloth
bash setup_vast.sh              # On training server
python create_balanced_dataset.py
python train.py
```

**Output**: Fine-tuned LoRA adapters

---

### 2. Export & Quantization (`finetunedmodels/`)

**Purpose**: Convert and optimize models for deployment

**Process**:
1. Merge LoRA with base model (3.46 GB)
2. Convert to GGUF format
3. Quantize to Q4_K_M (1.05 GB)

**Scripts**:
```bash
python merge_lora.py                    # Merge adapters
python export_and_quantize.py           # Export & prepare
bash quantize_to_gguf.sh                # Quantize
bash download_model.sh                  # Download
```

**Output**: Production-ready GGUF model

---

### 3. Deployment (`serverhost/`)

**Purpose**: Host the model with web interfaces

**Components**:
- **llama.cpp server** (Port 8080) - AI chat interface
- **Upload UI** (Port 3000) - Model management

**Quick Start**:
```bash
cd serverhost
bash setup.sh
# Open http://localhost:3000 and http://localhost:8080
```

**Configured For**:
- CPU-only inference (6 cores, 8GB RAM)
- Docker-based deployment
- Multiple model support

---

## 🔄 Complete Workflow

### Step 1: Train Your Model

```bash
# On training server (e.g., vast.ai with A100)
cd unsloth
python create_balanced_dataset.py
python train.py
```

**Duration**: ~48 minutes (3 epochs)  
**Output**: `output_model/` with LoRA adapters

### Step 2: Export & Quantize

```bash
# On training server
python merge_lora.py                           # → output_model_merged/ (3.46 GB)
python llama.cpp/convert_hf_to_gguf.py ...     # → FP16 GGUF (3.44 GB)
./llama.cpp/build/bin/llama-quantize ...       # → Q4_K_M GGUF (1.05 GB)
```

**Output**: `qwen3-1.7b-trading-Q4_K_M.gguf`

### Step 3: Download Model

```bash
# From local machine
rsync -avz server:/path/to/model.gguf finetunedmodels/
```

### Step 4: Deploy

```bash
# On deployment server (or local)
cd serverhost
bash setup.sh

# Access:
# - Upload UI: http://localhost:3000
# - Chat UI: http://localhost:8080
```

---

## 🎮 Usage Examples

### Training a New Model

```bash
# 1. Prepare data
cd unsloth
python create_balanced_dataset.py

# 2. Train
python train.py

# 3. Export
python merge_lora.py
python export_and_quantize.py

# 4. Quantize
bash quantize_to_gguf.sh

# 5. Download
bash download_model.sh
```

### Deploying a Model

```bash
# 1. Copy model to serverhost
cp finetunedmodels/your-model/*.gguf serverhost/models/

# 2. Setup and run
cd serverhost
bash setup.sh

# 3. Open browser
open http://localhost:3000  # Management
open http://localhost:8080  # Chat
```

### Switching Models

```bash
# Option 1: Via Upload UI
# - Visit http://localhost:3000
# - Click "Activate" on desired model
# - Restart: docker compose restart llama-server

# Option 2: Via CLI
cd serverhost/models
ln -sf new-model.gguf current.gguf
docker compose restart llama-server
```

---

## 📊 Resource Requirements

### Training (Recommended)

- **GPU**: NVIDIA A100 40GB (or similar)
- **RAM**: 32GB+
- **Storage**: 50GB
- **Time**: ~1 hour per training run

### Deployment (Your Setup)

- **CPU**: 6 cores
- **RAM**: 8GB
- **Storage**: ~2GB per model
- **Performance**: 2-8 tokens/sec

---

## 🔧 Configuration Files

### Key Files to Customize

**Training**:
- `unsloth/train.py` - Training hyperparameters
- `unsloth/.env` - API keys (HF_TOKEN, WANDB_API_KEY)
- `unsloth/data/` - Your training data

**Deployment**:
- `serverhost/docker-compose.yml` - Server settings
- CPU threads, memory limits, context size
- Port mappings

---

## 🎯 Typical Use Cases

### 1. Domain-Specific Assistant

Train on your domain data → Deploy for internal use

```
Your Data → Training → Export → Deploy → Team Access
```

### 2. Multiple Versions

Train different versions → Switch via Upload UI

```
Model v1.0 ──┐
Model v1.1 ──┼──→ Upload UI → Activate → Use
Model v2.0 ──┘
```

### 3. Continuous Improvement

Retrain with new data → Update deployment

```
New Data → Retrain → Export → Upload → Switch
```

---

## 📚 Documentation Index

| Component | Guide | Description |
|-----------|-------|-------------|
| Training | `unsloth/README.md` | Setup & training |
| Post-Training | `unsloth/POST_TRAINING.md` | Export & quantize |
| Model Info | `finetunedmodels/.../README.md` | Model details |
| Deployment | `serverhost/README.md` | Full deployment guide |
| Quick Start | `serverhost/QUICKSTART.md` | 3-minute setup |

---

## 🆘 Quick Help

### Training Issues

```bash
cd unsloth
# Check environment
python check_env.py

# Fix PyTorch
bash fix_torchvision.sh

# View logs
tail -f training_balanced.log
```

### Deployment Issues

```bash
cd serverhost
# Check services
docker compose ps

# View logs
docker compose logs -f

# Restart
docker compose restart
```

### Model Issues

```bash
# Verify GGUF file
file models/current.gguf

# Test loading
./llama.cpp/build/bin/llama-cli -m models/current.gguf -p "test"

# Check size
ls -lh models/*.gguf
```

---

## 🚀 Performance Tips

### Training

- Use Flash Attention 2 (enabled by default)
- Enable packing for better GPU utilization
- Balance dataset to prevent catastrophic forgetting
- Monitor with WandB

### Inference (CPU)

- Use Q4_K_M quantization (best balance)
- Limit context to 2048-4096 tokens
- Single concurrent user
- Monitor with `docker stats`

---

## 🔒 Security Considerations

### Training Server

- Use environment variables for tokens
- Don't commit `.env` files
- Secure vast.ai/training instance

### Deployment Server

- Currently: No authentication (localhost only)
- Production: Add reverse proxy + auth
- Use firewall rules
- Enable HTTPS for external access

---

## 📈 Monitoring

### Training

```bash
# WandB dashboard
https://wandb.ai/your-project

# Local logs
tail -f unsloth/training_balanced.log
```

### Deployment

```bash
# Container stats
docker stats

# Server logs
docker compose logs -f llama-server

# API health
curl http://localhost:8080/health
```

---

## 🎉 Success Checklist

- [ ] **Trained** model on GPU server
- [ ] **Exported** to GGUF format
- [ ] **Quantized** to Q4_K_M
- [ ] **Downloaded** to local machine
- [ ] **Deployed** with Docker
- [ ] **Accessed** both UIs (3000 & 8080)
- [ ] **Tested** chat functionality
- [ ] **Verified** tool-calling works

---

## 📞 Support Resources

- **llama.cpp**: https://github.com/ggml-org/llama.cpp
- **Unsloth**: https://github.com/unslothai/unsloth
- **WandB**: https://wandb.ai
- **Docker**: https://docs.docker.com

---

## 🎓 Learning Path

1. **Start**: Run `serverhost/setup.sh` → Try the chat
2. **Explore**: Upload different models via UI
3. **Customize**: Adjust settings in docker-compose.yml
4. **Train**: Create your own dataset → Fine-tune
5. **Scale**: Deploy on production server

---

**Made with ❤️ for the AI community**

Questions? Check the README files in each directory!

