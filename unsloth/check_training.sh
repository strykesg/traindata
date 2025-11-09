#!/bin/bash
# Check training status on vast.ai server
# Run this from your LOCAL machine

SERVER_HOST="157.90.56.162"
SERVER_PORT="32613"
SERVER_USER="root"

echo "================================================================================"
echo "Training Status Check"
echo "================================================================================"

# Check if training is running
echo ""
echo "🔍 Checking for running training process..."
TRAINING_PID=$(ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
    "pgrep -f 'python train.py'" 2>/dev/null)

if [ -n "$TRAINING_PID" ]; then
    echo "✓ Training is RUNNING (PID: ${TRAINING_PID})"
    
    # Get training duration
    echo ""
    echo "⏱️  Process information:"
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
        "ps -p ${TRAINING_PID} -o pid,etime,pmem,cmd" 2>/dev/null || true
else
    echo "⚠️  Training is NOT running"
fi

# Check latest log file
echo ""
echo "📋 Latest log entries:"
echo "--------------------------------------------------------------------------------"
ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
    "tail -30 /workspace/traindata/unsloth/training*.log 2>/dev/null | tail -30" || \
    echo "No log file found"

# Check if output model exists
echo ""
echo "--------------------------------------------------------------------------------"
echo "📦 Model output status:"
OUTPUT_EXISTS=$(ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
    "[ -d /workspace/traindata/unsloth/output_model ] && echo 'yes' || echo 'no'")

if [ "$OUTPUT_EXISTS" = "yes" ]; then
    echo "✓ Output model directory exists"
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
        "ls -lh /workspace/traindata/unsloth/output_model/*.safetensors 2>/dev/null | wc -l | xargs echo '  Model files:'"
else
    echo "⚠️  No output model directory yet"
fi

# Check GPU usage
echo ""
echo "🎮 GPU Status:"
echo "--------------------------------------------------------------------------------"
ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} \
    "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits" 2>/dev/null || \
    echo "Could not query GPU status"

echo ""
echo "================================================================================"

# Estimate completion time if training is running
if [ -n "$TRAINING_PID" ]; then
    echo ""
    echo "💡 To see live training progress:"
    echo "   ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} 'tail -f /workspace/traindata/unsloth/training*.log'"
    echo ""
    echo "💡 To stop training:"
    echo "   ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} 'pkill -f python train.py'"
fi

echo "================================================================================"

