# llama.cpp Server Hosting Setup

Docker-based deployment for llama.cpp with a beautiful WebUI and model management interface.

## 🎯 What You Get

This setup provides **two separate interfaces**:

1. **🚀 llama.cpp WebUI** (Port 8080)
   - Official llama.cpp chat interface
   - Document processing (PDF, text files)
   - Image understanding
   - Advanced sampling controls
   - Full-featured AI chat

2. **📤 Model Upload UI** (Port 3000)
   - Upload GGUF models
   - Manage multiple models
   - Switch active models
   - Monitor server status

## ⚙️ System Requirements

**Current Configuration:**
- **CPU**: 6 cores (5 threads used for inference)
- **RAM**: 8GB total (7GB max for container)
- **Storage**: ~1-2GB per Q4_K_M model

**Optimized For:**
- CPU-only inference
- Low memory footprint
- Single concurrent user
- Q4_K_M quantized models

## 🚀 Quick Start

### 1. Copy Your Model

First, copy your fine-tuned model to the models directory:

```bash
# From the project root
cp finetunedmodels/qwen3-1.7b-trading-q4km/qwen3-1.7b-trading-Q4_K_M.gguf \
   serverhost/models/qwen3-trading.gguf

# Set it as the active model
cd serverhost/models
ln -s qwen3-trading.gguf current.gguf
```

### 2. Start the Services

```bash
cd serverhost
docker-compose up -d
```

### 3. Access the Interfaces

- **📤 Upload UI**: http://localhost:3000
- **🚀 llama.cpp WebUI**: http://localhost:8080

## 📋 Detailed Setup

### Directory Structure

```
serverhost/
├── docker-compose.yml        # Main configuration
├── models/                    # Your GGUF models go here
│   ├── qwen3-trading.gguf    # Your model
│   └── current.gguf          # Symlink to active model
├── upload-ui/                 # Model management UI
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
└── README.md                  # This file
```

### Configuration Details

**CPU-Only Settings:**
- `--threads 5`: Use 5 cores for inference (leave 1 for system)
- `--threads-batch 5`: Prompt processing threads
- `--n-gpu-layers 0`: No GPU acceleration
- `--ctx-size 4096`: Context window (adjust based on RAM)
- `--parallel 2`: Handle 2 concurrent requests max

**Memory Management:**
- Container limit: 7GB
- `--mlock`: Lock model in RAM (prevents swapping)
- `--no-mmap`: Load entire model to RAM for better CPU performance

## 🎮 Usage Guide

### Using the Upload UI (Port 3000)

1. **Upload a Model:**
   - Click "Choose GGUF File"
   - Select your `.gguf` model
   - Click "Upload Model"

2. **Activate a Model:**
   - Click "Activate" on any uploaded model
   - Restart the server: `docker-compose restart llama-server`

3. **Delete a Model:**
   - Click "Delete" (cannot delete active model)

4. **Open llama.cpp WebUI:**
   - Click "🚀 Open llama.cpp WebUI" button
   - Or visit http://localhost:8080

### Using llama.cpp WebUI (Port 8080)

The official llama.cpp WebUI includes:

- **💬 Chat**: Full-featured AI conversation
- **📄 Documents**: Upload PDFs, text files, code
- **🖼️ Images**: Vision model support (if model supports it)
- **⚙️ Settings**: Advanced sampling controls
- **💾 Sessions**: Save and load conversations

**Recommended Settings for CPU:**
- Temperature: 0.7
- Top-P: 0.9
- Context: 2048-4096 tokens
- Parallel requests: 1-2

## 🔧 Common Tasks

### Check Service Status

```bash
docker-compose ps
docker-compose logs -f llama-server  # View logs
```

### Restart Services

```bash
docker-compose restart              # Restart all
docker-compose restart llama-server # Restart server only
```

### Stop Services

```bash
docker-compose down                 # Stop all
docker-compose down -v              # Stop and remove volumes
```

### Update Services

```bash
docker-compose pull                 # Pull latest images
docker-compose up -d --build        # Rebuild and restart
```

### Copy Model from Remote Server

If you're deploying to a remote server:

```bash
# From your local machine
scp finetunedmodels/qwen3-1.7b-trading-q4km/qwen3-1.7b-trading-Q4_K_M.gguf \
    user@server:/path/to/serverhost/models/qwen3-trading.gguf

# Then on the server
ssh user@server
cd /path/to/serverhost/models
ln -sf qwen3-trading.gguf current.gguf
cd ..
docker-compose restart llama-server
```

## ⚡ Performance Tips

### For Your 6-Core, 8GB Setup:

1. **Use Q4_K_M models** (best balance for CPU)
2. **Keep context small** (2048-4096 tokens)
3. **Single user at a time** (parallel=2 setting)
4. **Monitor memory**: `docker stats llama-cpp-server`

### Expected Performance:

- **Prompt Processing**: ~5-15 tokens/sec
- **Generation**: ~2-8 tokens/sec
- **Model Load Time**: 5-10 seconds

### If You Need More Speed:

1. Reduce context size:
   ```yaml
   --ctx-size 2048
   ```

2. Use smaller models (if available):
   - 1B-1.7B models work best on CPU
   - Q4_K_M or Q5_K_M quantization

3. Reduce threads if system is slow:
   ```yaml
   --threads 4
   ```

## 🐛 Troubleshooting

### Server Won't Start

```bash
# Check logs
docker-compose logs llama-server

# Common issues:
# 1. Model file missing
ls -lh models/current.gguf

# 2. Port already in use
lsof -i :8080

# 3. Not enough memory
docker stats
```

### Out of Memory

Reduce context size in `docker-compose.yml`:

```yaml
--ctx-size 2048  # or even 1024
```

### Slow Response

1. Check CPU usage: `htop`
2. Reduce parallel requests: `--parallel 1`
3. Use smaller quantization (Q4_0 instead of Q4_K_M)

### Upload UI Can't Connect

```bash
# Check if llama-server is running
curl http://localhost:8080/health

# Check network
docker network ls
docker network inspect llama-network
```

## 📊 Monitoring

### Check Resource Usage

```bash
# Container stats
docker stats

# Detailed logs
docker-compose logs -f --tail=100

# Server health
curl http://localhost:8080/health
```

### API Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Model info
curl http://localhost:8080/v1/models

# Server slots
curl http://localhost:8080/slots
```

## 🔒 Security Notes

**Current Setup:**
- Binds to all interfaces (0.0.0.0)
- No authentication
- No HTTPS

**For Production:**

1. Use reverse proxy (nginx, Caddy)
2. Add authentication
3. Enable HTTPS
4. Bind to localhost only
5. Use firewall rules

Example nginx config snippet:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📚 Additional Resources

- [llama.cpp Documentation](https://github.com/ggml-org/llama.cpp)
- [llama.cpp WebUI Guide](https://github.com/ggml-org/llama.cpp/discussions/16938)
- [llama-server Documentation](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
- [GGUF Format](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify model format: `file models/current.gguf`
3. Test with smaller model first
4. Check system resources: `free -h` and `htop`

## 📝 Configuration Reference

### Key llama-server Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--threads` | 5 | CPU threads for generation |
| `--threads-batch` | 5 | Threads for prompt processing |
| `--ctx-size` | 4096 | Context window size |
| `--parallel` | 2 | Max concurrent requests |
| `--n-gpu-layers` | 0 | GPU layers (0 = CPU only) |
| `--mlock` | enabled | Lock model in RAM |
| `--no-mmap` | enabled | Load to RAM (better for CPU) |

### Adjusting for Different Hardware

**More RAM (16GB+):**
```yaml
--ctx-size 8192
--parallel 4
memory: 14G
```

**Fewer Cores (4 cores):**
```yaml
--threads 3
--threads-batch 3
cpus: '4'
```

**Less RAM (6GB):**
```yaml
--ctx-size 2048
--parallel 1
memory: 5G
```

## 🎉 You're All Set!

Your llama.cpp server is now ready to use. Enjoy your locally-hosted AI!

