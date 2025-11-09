# Model Persistence Across Redeploys

This setup ensures that uploaded models and the active model selection persist across container restarts and redeployments.

## 🔄 How It Works

### **State Persistence**

1. **Active Model State File**: `.active_model` stores the name of the currently active model
2. **Symlink**: `current.gguf` → points to the active model file
3. **Init Script**: Runs on every container start to restore the active model

### **On Startup**

When `llama-server` container starts:

1. ✅ Checks if `current.gguf` exists
2. ✅ If missing, reads `.active_model` file
3. ✅ Restores the symlink to the saved model
4. ✅ If no saved state, uses first available `.gguf` file
5. ✅ Starts llama-server with the active model

### **On Model Activation**

When you activate a model via Upload UI:

1. ✅ Creates `current.gguf` symlink
2. ✅ Saves model name to `.active_model` file
3. ✅ Both persist across redeploys

## 📁 Files Involved

```
models/
├── qwen3-trading.gguf          # Your uploaded model
├── other-model.gguf            # Another model
├── current.gguf                # Symlink → qwen3-trading.gguf
├── .active_model               # State file: "qwen3-trading.gguf"
└── init-models.sh              # Initialization script
```

## 🔧 Components

### **1. Init Script** (`models/init-models.sh`)

Runs on container startup to:
- Restore active model from state file
- Create symlink if missing
- Validate model files exist
- Set first available model if no state

### **2. Entrypoint Wrapper** (`entrypoint.sh`)

Runs before llama-server to:
- Execute init script
- Verify model exists
- Start llama-server with proper model

### **3. Upload UI** (`upload-ui/app.py`)

Saves state when activating models:
- Creates symlink
- Writes to `.active_model` file
- Ensures persistence

## ✅ What Persists

After redeploy (`docker compose down && docker compose up -d`):

- ✅ All uploaded `.gguf` model files
- ✅ Active model selection (via `.active_model`)
- ✅ Symlink `current.gguf`
- ✅ Model state and configuration

## 🚨 Troubleshooting

### **Model Not Found After Redeploy**

```bash
# Check if models exist
ls -lh models/*.gguf

# Check state file
cat models/.active_model

# Check symlink
ls -la models/current.gguf

# Manually restore
cd models
ln -sf your-model.gguf current.gguf
echo "your-model.gguf" > .active_model
```

### **Init Script Not Running**

```bash
# Check entrypoint logs
docker compose logs llama-server | grep -i init

# Verify entrypoint is mounted
docker compose exec llama-server ls -la /entrypoint.sh

# Check init script exists
docker compose exec llama-server ls -la /models/init-models.sh
```

### **Manual Model Activation**

```bash
# SSH into container
docker compose exec llama-server bash

# Run init script manually
bash /models/init-models.sh

# Or manually set active model
cd /models
ln -sf your-model.gguf current.gguf
echo "your-model.gguf" > .active_model
```

## 📝 Example Workflow

### **1. Upload Model**
```
Upload UI → Upload qwen3-trading.gguf
```

### **2. Activate Model**
```
Upload UI → Click "Activate" → Creates symlink + saves state
```

### **3. Redeploy**
```bash
docker compose down
docker compose up -d
```

### **4. Verify Persistence**
```bash
# Check logs show model restored
docker compose logs llama-server | grep "Active Model"

# Verify symlink
ls -la models/current.gguf

# Test API
curl http://localhost:8080/v1/models
```

## 🎯 Best Practices

1. **Always activate via Upload UI** - ensures state is saved
2. **Check logs after redeploy** - verify model restored correctly
3. **Keep `.active_model` file** - don't delete it manually
4. **Backup models directory** - before major changes

## 🔍 Verification Commands

```bash
# Check active model
cat models/.active_model

# Verify symlink
readlink -f models/current.gguf

# List all models
ls -lh models/*.gguf

# Check container logs
docker compose logs llama-server | tail -50
```

## 📊 State File Format

The `.active_model` file contains a single line with the model filename:

```
qwen3-trading.gguf
```

This is automatically created/updated when you activate a model via the Upload UI.

---

**Your models will now persist across all redeployments!** 🎉

