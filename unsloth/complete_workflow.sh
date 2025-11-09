#!/bin/bash
# Complete post-training workflow
# Run this on the TRAINING SERVER after training completes

set -e

echo "================================================================================"
echo "Complete Post-Training Workflow"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Export the trained model"
echo "  2. Quantize to Q4_K_M GGUF format"
echo "  3. Prepare for download"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Export model
echo ""
echo "================================================================================"
echo "Step 1: Exporting Model"
echo "================================================================================"
python export_and_quantize.py

if [ $? -ne 0 ]; then
    echo "❌ Export failed!"
    exit 1
fi

# Step 2: Quantize
echo ""
echo "================================================================================"
echo "Step 2: Quantizing to GGUF"
echo "================================================================================"
bash quantize_to_gguf.sh

if [ $? -ne 0 ]; then
    echo "❌ Quantization failed!"
    exit 1
fi

# Step 3: Summary
echo ""
echo "================================================================================"
echo "✅ All Processing Complete!"
echo "================================================================================"
echo ""
echo "📦 Model ready for download in: finetunedmodels/"
echo ""
echo "Next steps (run on your LOCAL machine):"
echo "  1. Download the model:"
echo "     bash download_model.sh"
echo ""
echo "  2. Or manually with rsync:"
echo "     rsync -avz -e 'ssh -p 32613' root@157.90.56.162:/workspace/traindata/unsloth/finetunedmodels/ ./downloaded_models/"
echo ""
echo "================================================================================"

# Display final directory listing
echo ""
echo "📋 Final file listing:"
LATEST_MODEL=$(ls -td finetunedmodels/qwen3-1.7b-trading-bot-* | head -1)
if [ -n "$LATEST_MODEL" ]; then
    ls -lh "$LATEST_MODEL"
    echo ""
    du -sh "$LATEST_MODEL"
fi

