# Upload Persistence & Boot Initialization

## ✅ What Was Fixed

### **1. Upload Persistence**

**Problem:** Uploads weren't persisting correctly or files weren't being saved properly.

**Solution:**
- ✅ **Chunked writing** - Files are written in 1MB chunks for better reliability
- ✅ **Explicit flushing** - Data is flushed to disk every 100MB during upload
- ✅ **Final sync** - `os.fsync()` ensures all data is written to disk before completion
- ✅ **Size verification** - Checks file size matches expected size
- ✅ **Permission setting** - Sets proper file permissions (644) after save
- ✅ **Error cleanup** - Removes partial files on error

### **2. Boot Initialization**

**Problem:** Models directory might not be initialized correctly on container startup.

**Solution:**
- ✅ **Startup script** (`start.sh`) - Verifies directory exists and is writable
- ✅ **Python initialization** - `initialize_models_directory()` runs on app import
- ✅ **Directory verification** - Checks permissions and lists existing models
- ✅ **Health checks** - Both containers have health checks

### **3. Model Detection**

**Problem:** Uploaded models weren't showing in the UI.

**Solution:**
- ✅ **Improved `get_models()`** - Better error handling and debugging
- ✅ **Directory verification** - Checks directory on each request
- ✅ **Detailed logging** - Logs all models found
- ✅ **API verification** - `/api/verify/<model>` endpoint to check file status

---

## 🔧 How It Works

### **On Container Startup:**

1. **Startup Script** (`start.sh`):
   ```bash
   - Creates models directory
   - Checks write permissions
   - Lists existing models
   - Starts Flask app
   ```

2. **Python Initialization** (`initialize_models_directory()`):
   ```python
   - Ensures directory exists
   - Verifies write permissions
   - Lists all existing .gguf files
   - Logs initialization status
   ```

### **During Upload:**

1. **File Reception**:
   - Validates file type (.gguf only)
   - Checks file size
   - Secures filename

2. **Chunked Writing**:
   - Reads file in 1MB chunks
   - Writes to disk
   - Flushes every 100MB
   - Shows progress in logs

3. **Persistence**:
   - Final `os.fsync()` to ensure disk write
   - Sets file permissions
   - Verifies file exists and size matches

4. **Verification**:
   - JavaScript verifies file exists via API
   - Shows success/error message
   - Refreshes model list

---

## 📋 Files Modified

1. **`upload-ui/app.py`**:
   - Added `initialize_models_directory()` function
   - Improved upload persistence with chunked writing
   - Added explicit `os.fsync()` calls
   - Better error handling and logging

2. **`upload-ui/start.sh`**:
   - New startup script
   - Verifies directory on boot
   - Lists existing models

3. **`upload-ui/Dockerfile`**:
   - Added curl for healthcheck
   - Uses startup script instead of direct Python call

4. **`docker-compose.yml`**:
   - Added healthcheck for upload-ui
   - Explicit `rw` mount for models directory
   - Added `init: true` for proper signal handling

---

## 🚀 To Apply Changes

```bash
cd serverhost

# Rebuild upload-ui with new changes
docker compose build upload-ui

# Restart containers
docker compose down
docker compose up -d

# Watch logs to see initialization
docker compose logs -f upload-ui
```

---

## ✅ Verification

### **Check Initialization:**

```bash
# Should see initialization logs
docker compose logs upload-ui | grep "Upload UI Initialization"

# Should see models listed
docker compose logs upload-ui | grep "Found.*existing model"
```

### **Test Upload:**

1. Upload a model via http://localhost:3000
2. Watch logs: `docker compose logs -f upload-ui`
3. Should see:
   - File received
   - Chunked writing progress
   - Final sync
   - Verification

### **Verify Persistence:**

```bash
# Check file exists in container
docker compose exec upload-ui ls -lh /app/models/

# Check file exists on host
ls -lh models/

# Check llama-server can see it
docker compose exec llama-server ls -lh /models/
```

---

## 🔍 Debugging

### **If uploads still don't persist:**

1. **Check logs:**
   ```bash
   docker compose logs upload-ui | tail -100
   ```

2. **Check directory permissions:**
   ```bash
   docker compose exec upload-ui ls -ld /app/models
   docker compose exec upload-ui touch /app/models/test.txt
   ```

3. **Check disk space:**
   ```bash
   docker compose exec upload-ui df -h
   ```

4. **Verify volume mount:**
   ```bash
   docker compose exec upload-ui mount | grep models
   ```

---

## 📊 Expected Behavior

### **On Startup:**
```
============================================================
Upload UI Initialization
============================================================
✓ Models directory ensured: /app/models
✓ Models directory is writable
✓ Found X existing model(s):
  - model1.gguf (X.XX GB)
  - model2.gguf (X.XX GB)
============================================================
```

### **During Upload:**
```
==================================================
UPLOAD REQUEST RECEIVED
==================================================
MODELS_DIR: /app/models
MODELS_DIR exists: True
MODELS_DIR is writable: True
File size: X bytes (X.XX GB)
Saving to: /app/models/model.gguf
  Progress: 0.10 GB written...
  Progress: 0.20 GB written...
✓ File.save() completed with explicit persistence
✓ File saved successfully!
  Size: X bytes (X.XX GB)
✓ File permissions set: 0o644
==================================================
```

---

## 🎯 Key Features

- ✅ **Guaranteed persistence** - Files are synced to disk
- ✅ **Boot verification** - Directory checked on startup
- ✅ **Error recovery** - Partial files cleaned up on error
- ✅ **Progress tracking** - Logs show upload progress
- ✅ **Size verification** - Ensures complete uploads
- ✅ **Permission management** - Sets proper file permissions

---

**Your uploads will now persist correctly across container restarts!** 🎉

