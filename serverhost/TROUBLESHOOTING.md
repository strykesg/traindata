# Troubleshooting Guide

## Entrypoint Script Issues

### Error: `exec: --: invalid option`

**Symptoms:**
```
/entrypoint.sh: line 52: exec: --: invalid option
exec: usage: exec [-cl] [-a name] [command [argument ...]] [redirection ...]
```

**Solution:**

1. **Ensure entrypoint script is updated:**
   ```bash
   # Check the script exists and is executable
   ls -la entrypoint.sh
   chmod +x entrypoint.sh
   ```

2. **Restart the container to pick up changes:**
   ```bash
   docker compose down
   docker compose up -d
   ```

3. **Check logs:**
   ```bash
   docker compose logs llama-server
   ```

4. **Verify entrypoint is mounted:**
   ```bash
   docker compose exec llama-server ls -la /entrypoint.sh
   docker compose exec llama-server cat /entrypoint.sh | head -20
   ```

### Container Keeps Restarting

**Check:**
- Model file exists: `ls -lh models/current.gguf`
- Init script exists: `ls -lh models/init-models.sh`
- Check logs: `docker compose logs llama-server`

### Model Not Found After Redeploy

**Solution:**
1. Check state file: `cat models/.active_model`
2. Verify symlink: `ls -la models/current.gguf`
3. Run init manually:
   ```bash
   docker compose exec llama-server bash /models/init-models.sh
   ```

## Common Issues

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8080
lsof -i :3000

# Kill the process or change ports in docker-compose.yml
```

### Out of Memory

```bash
# Check memory usage
docker stats llama-cpp-server

# Reduce context size in docker-compose.yml
--ctx-size 2048  # instead of 64328
```

### Upload Fails

```bash
# Check upload-ui logs
docker compose logs upload-ui

# Verify file size limit (10GB max)
# Check disk space
df -h
```

## Debug Commands

```bash
# View all logs
docker compose logs -f

# Check container status
docker compose ps

# Execute commands in container
docker compose exec llama-server bash
docker compose exec upload-ui bash

# Check network
docker network inspect llama-network

# Check volumes
docker volume ls
```

## Reset Everything

```bash
# Stop and remove containers
docker compose down -v

# Remove models (careful!)
rm -rf models/*.gguf

# Restart fresh
docker compose up -d
```

