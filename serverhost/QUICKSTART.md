# 🚀 Quick Start Guide

Get your llama.cpp server running in 3 minutes!

## Prerequisites

- Docker Desktop installed
- Your fine-tuned GGUF model ready
- 8GB RAM available
- 6-core CPU

## 🎯 Three Simple Steps

### 1️⃣ Run Setup Script

```bash
cd serverhost
bash setup.sh
```

This will:
- ✅ Copy your model from `finetunedmodels/`
- ✅ Set up directories
- ✅ Build Docker containers
- ✅ Start all services

### 2️⃣ Access Your Interfaces

**Upload UI** (Model Management)  
http://localhost:3000

**llama.cpp WebUI** (AI Chat)  
http://localhost:8080

### 3️⃣ Start Chatting!

Open the llama.cpp WebUI and start using your fine-tuned trading bot!

---

## 🔧 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Copy your model
cp ../finetunedmodels/qwen3-1.7b-trading-q4km/qwen3-1.7b-trading-Q4_K_M.gguf \
   models/qwen3-trading.gguf

# 2. Set as active
cd models && ln -s qwen3-trading.gguf current.gguf && cd ..

# 3. Start services
docker compose up -d
```

---

## 📊 System Overview

```
┌─────────────────────────────────────┐
│   Your Computer (8GB RAM, 6 cores) │
├─────────────────────────────────────┤
│                                     │
│  Docker Container: llama-server     │
│  ├─ Port 8080 (WebUI)              │
│  ├─ CPU-only inference             │
│  └─ Loads current.gguf             │
│                                     │
│  Docker Container: upload-ui        │
│  ├─ Port 3000 (Management)         │
│  └─ Model upload/switching         │
│                                     │
└─────────────────────────────────────┘
```

---

## 💡 Common Commands

```bash
# View logs
docker compose logs -f

# Restart server (after model change)
docker compose restart llama-server

# Stop everything
docker compose down

# Check status
docker compose ps

# View resource usage
docker stats
```

---

## 🎮 Using the Upload UI

1. **Open** http://localhost:3000
2. **Upload** new GGUF models
3. **Activate** a model
4. **Restart** the llama-server
5. **Click** "Open llama.cpp WebUI"

---

## 🦙 Using llama.cpp WebUI

1. **Open** http://localhost:8080
2. **Start** chatting immediately
3. **Upload** documents for context
4. **Adjust** settings in sidebar
5. **Save** conversations

---

## ⚡ Performance Expectations

**Your Setup (6 cores, 8GB RAM):**
- Prompt processing: ~5-15 tokens/sec
- Generation: ~2-8 tokens/sec
- Model load: ~5-10 seconds
- Max context: 4096 tokens

**Tips for Better Performance:**
- Use Q4_K_M models (you already are!)
- Keep context under 2048 tokens
- Single user at a time
- Close other heavy applications

---

## 🆘 Troubleshooting

### Server won't start?

```bash
# Check logs
docker compose logs llama-server

# Verify model exists
ls -lh models/current.gguf

# Restart with fresh state
docker compose down -v
docker compose up -d
```

### Out of memory?

Edit `docker-compose.yml` and reduce context:
```yaml
--ctx-size 2048  # or even 1024
```

### Can't access WebUI?

```bash
# Check if port is in use
lsof -i :8080

# Try different port
# Edit docker-compose.yml: "8081:8080"
```

---

## 📚 Full Documentation

For detailed information, see:
- **[README.md](README.md)** - Complete guide
- **[docker-compose.yml](docker-compose.yml)** - Configuration
- **[llama.cpp docs](https://github.com/ggml-org/llama.cpp)** - Official docs

---

## ✅ Checklist

- [ ] Docker Desktop is running
- [ ] Ran `bash setup.sh`
- [ ] Both containers are up (check with `docker compose ps`)
- [ ] Can access http://localhost:3000
- [ ] Can access http://localhost:8080
- [ ] Model is loaded (check logs)

---

🎉 **You're ready to go!** Start chatting with your fine-tuned trading bot at http://localhost:8080

