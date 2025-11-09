#!/bin/bash
# Quantize fine-tuned model to GGUF Q4_K_M format
# Runs on the training server

set -e

echo "================================================================================"
echo "Model Quantization to GGUF (Q4_K_M)"
echo "================================================================================"

# Configuration
EXPORT_DIR="finetunedmodels"
LLAMA_CPP_DIR="llama.cpp"

# Find the latest model directory
LATEST_MODEL=$(ls -td ${EXPORT_DIR}/qwen3-1.7b-trading-bot-* 2>/dev/null | head -1)

if [ -z "$LATEST_MODEL" ]; then
    echo "❌ Error: No exported model found in ${EXPORT_DIR}/"
    echo "   Please run export_and_quantize.py first"
    exit 1
fi

echo "📦 Found model: ${LATEST_MODEL}"
MODEL_NAME=$(basename "$LATEST_MODEL")

# Step 1: Check/Install llama.cpp
echo ""
echo "🔧 Step 1: Setting up llama.cpp..."
if [ ! -d "$LLAMA_CPP_DIR" ]; then
    echo "   Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
    echo "   Building llama.cpp..."
    make -j$(nproc)
    cd ..
    echo "   ✓ llama.cpp installed"
else
    echo "   ✓ llama.cpp already installed"
    cd llama.cpp
    git pull origin master || true
    make -j$(nproc) || true
    cd ..
fi

# Step 2: Install required Python packages
echo ""
echo "📦 Step 2: Installing conversion dependencies..."
pip install -q gguf numpy sentencepiece protobuf || true
echo "   ✓ Dependencies ready"

# Step 3: Convert to FP16 GGUF first
echo ""
echo "🔄 Step 3: Converting to FP16 GGUF..."
FP16_GGUF="${LATEST_MODEL}/${MODEL_NAME}-FP16.gguf"

python llama.cpp/convert_hf_to_gguf.py \
    "${LATEST_MODEL}" \
    --outfile "${FP16_GGUF}" \
    --outtype f16

if [ $? -eq 0 ]; then
    echo "   ✓ FP16 GGUF created"
else
    echo "   ❌ Error creating FP16 GGUF"
    exit 1
fi

# Step 4: Quantize to Q4_K_M
echo ""
echo "⚡ Step 4: Quantizing to Q4_K_M (optimal quality/size)..."
Q4_GGUF="${LATEST_MODEL}/${MODEL_NAME}-Q4_K_M.gguf"

./llama.cpp/llama-quantize \
    "${FP16_GGUF}" \
    "${Q4_GGUF}" \
    Q4_K_M

if [ $? -eq 0 ]; then
    echo "   ✓ Q4_K_M quantization complete"
else
    echo "   ❌ Error during quantization"
    exit 1
fi

# Step 5: Calculate sizes
echo ""
echo "💾 Step 5: Size comparison..."
FP16_SIZE=$(du -h "${FP16_GGUF}" | cut -f1)
Q4_SIZE=$(du -h "${Q4_GGUF}" | cut -f1)
echo "   FP16 GGUF: ${FP16_SIZE}"
echo "   Q4_K_M GGUF: ${Q4_SIZE}"

# Calculate compression ratio
FP16_BYTES=$(stat -f%z "${FP16_GGUF}" 2>/dev/null || stat -c%s "${FP16_GGUF}")
Q4_BYTES=$(stat -f%z "${Q4_GGUF}" 2>/dev/null || stat -c%s "${Q4_GGUF}")
RATIO=$(echo "scale=2; ${Q4_BYTES} / ${FP16_BYTES} * 100" | bc)
echo "   Compression: ${RATIO}% of original size"

# Step 6: Test the quantized model (optional)
echo ""
echo "🧪 Step 6: Testing quantized model..."
echo "   Running quick inference test..."
./llama.cpp/llama-cli \
    -m "${Q4_GGUF}" \
    -p "You are a helpful trading assistant." \
    -n 50 \
    --temp 0.7 \
    > /tmp/test_output.txt 2>&1

if [ $? -eq 0 ]; then
    echo "   ✓ Model loads and runs successfully"
else
    echo "   ⚠️  Warning: Model test had issues (may still work)"
fi

# Step 7: Create README for the quantized model
echo ""
echo "📝 Step 7: Creating quantization README..."
cat > "${LATEST_MODEL}/QUANTIZATION_INFO.md" << EOF
# Quantized Model Information

## Files
- **${MODEL_NAME}-FP16.gguf**: Full precision GGUF (${FP16_SIZE})
- **${MODEL_NAME}-Q4_K_M.gguf**: 4-bit quantized GGUF (${Q4_SIZE})

## Quantization Details
- **Method**: Q4_K_M (4-bit with K-means, medium variant)
- **Compression**: ${RATIO}% of FP16 size
- **Quality**: Minimal quality loss, excellent for most use cases
- **Speed**: ~2-4x faster inference than FP16

## Usage with llama.cpp
\`\`\`bash
./llama-cli -m ${MODEL_NAME}-Q4_K_M.gguf -p "Your prompt here" -n 512
\`\`\`

## Usage with Python (llama-cpp-python)
\`\`\`python
from llama_cpp import Llama

llm = Llama(model_path="${MODEL_NAME}-Q4_K_M.gguf", n_ctx=2048)
output = llm("Your prompt here", max_tokens=512)
print(output['choices'][0]['text'])
\`\`\`

## Recommended Settings
- Temperature: 0.7
- Top-p: 0.9
- Context: 2048 tokens
- Max tokens: 512-1024

## Performance
- Runs on CPU (no GPU required)
- ~1-10 tokens/sec on modern CPU
- ~50-200 tokens/sec on GPU with llama.cpp

Generated: $(date)
EOF

echo "   ✓ Documentation created"

echo ""
echo "================================================================================"
echo "✅ Quantization Complete!"
echo "================================================================================"
echo ""
echo "Model location: ${LATEST_MODEL}"
echo "Quantized file: ${MODEL_NAME}-Q4_K_M.gguf (${Q4_SIZE})"
echo ""
echo "Next step: Download the model"
echo "  bash download_model.sh"
echo ""
echo "================================================================================"

