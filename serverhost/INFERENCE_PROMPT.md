# Correct Inference Prompt Format

Your model was trained with `<reasoning>` and `<decision>` tags. To get proper output, you need to use the same format at inference time.

## System Prompt

When making API calls to your llama.cpp server, use this system message:

```
You are Dexter, a crypto trading bot assistant. Provide structured trading reasoning with decisions.
```

## Expected Output Format

The model should output:

```
<reasoning>
[Your reasoning text here]
</reasoning>

<decision>
{
  "action": "open_long",
  "parameters": {
    "asset": "BTC",
    "size": 0.5,
    "leverage": 5.0,
    "entry_price": 43500,
    "stop_loss": 42000,
    "take_profit": 46000
  },
  "confidence": 0.85,
  "reasoning_summary": "Summary here"
}
</decision>
```

## Example API Call

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bradllm",
    "messages": [
      {
        "role": "system",
        "content": "You are Dexter, a crypto trading bot assistant. Provide structured trading reasoning with decisions."
      },
      {
        "role": "user",
        "content": "Market context:\n{\n  \"mids\": {\"BTC\": 43500, \"ETH\": 2300},\n  \"key_indicators\": {\"BTC\": {\"rsi\": 65}}\n}\n\nAccount state:\n{\n  \"equity\": 10000,\n  \"leverage\": 5.0\n}\n\nWhat should we do?\nShould we go long on BTC with 5x leverage?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

## Fixing the Issue

If your model is outputting `<think>` or not closing tags:

1. **Always include the system prompt** - This matches the training format
2. **Use the exact system message** from training: `"You are Dexter, a crypto trading bot assistant. Provide structured trading reasoning with decisions."`
3. **Set appropriate max_tokens** - Make sure it's high enough (1000+) to allow the model to complete both tags
4. **Check stop sequences** - Don't set stop sequences that might cut off the closing tags

## llama.cpp Server Configuration

In your `docker-compose.yml`, you can add a default system prompt by modifying the command:

```yaml
command:
  - --host
  - 0.0.0.0
  - --port
  - "8080"
  - -m
  - /models/qwen3-1.7b-trading-Q4_K_M.gguf
  - --alias
  - bradllm
  - --ctx-size
  - "32768"
  # ... other flags ...
  - --system-prompt
  - "You are Dexter, a crypto trading bot assistant. Provide structured trading reasoning with decisions."
```

However, it's better to include the system prompt in each API call to match the training format exactly.

## Troubleshooting

If tags still aren't closing:

1. **Increase max_tokens** - The model might be hitting the token limit
2. **Check temperature** - Lower temperature (0.3-0.7) helps with structured output
3. **Add few-shot examples** - Include an example in the prompt showing the expected format
4. **Check training data** - Verify your training data has properly closed tags

## Few-Shot Example Prompt

If the model still struggles, try adding a few-shot example:

```
You are Dexter, a crypto trading bot assistant. Provide structured trading reasoning with decisions.

Example response format:
<reasoning>
[Detailed reasoning here]
</reasoning>

<decision>
{
  "action": "open_long",
  "parameters": {...},
  "confidence": 0.85,
  "reasoning_summary": "..."
}
</decision>

Now respond to the user's question using the same format.
```

