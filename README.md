# Synthetic Training Data Generator

High-speed, multi-worker system for generating synthetic crypto trading training data using OpenRouter models, with strict multi-stage validation.

## Features

- **Fast**: Auto-scaling workers (4-32), async I/O, batch operations
- **Strict**: 5-stage validation pipeline (schema, format, content)
- **Flexible**: Configurable models, worker counts, generation parameters
- **Robust**: Retry logic, error handling, progress tracking
- **Export-ready**: Direct output to LLaMA chat template format
- **Web UI**: Real-time progress monitoring with auto-refresh and download links

## Setup

1. **Clone and install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your OpenRouter API key and models
```

3. **Run generation:**
```bash
python main.py generate --count 10000
```

The web UI will automatically start on http://localhost:5000 showing:
- Real-time progress (valid/total examples)
- Latest generated example preview
- Time remaining estimate
- Download links for exported datasets

4. **Export to training format:**
```bash
python main.py export
```

Or use the web UI download buttons after export.

## Docker Deployment

### Using Docker Compose (Dokploy-compatible)

1. **Create `.env` file:**
```bash
cp .env.example .env
# Edit with your configuration
```

2. **Start the service:**
```bash
docker-compose up -d
```

3. **Access web UI:**
Open http://localhost:5000 in your browser to see real-time progress

4. **View logs:**
```bash
docker-compose logs -f
```

5. **Check statistics:**
```bash
docker-compose exec training-data-generator python main.py stats
```

6. **Export data:**
```bash
docker-compose exec training-data-generator python main.py export
```

Or use the download buttons in the web UI after export.

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `MODELS`: Comma-separated list of models (e.g., `anthropic/claude-3.5-sonnet,openai/gpt-4-turbo`)
- `MIN_WORKERS`: Minimum worker count (default: 4)
- `MAX_WORKERS`: Maximum worker count (default: 32)
- `BATCH_SIZE`: Database batch size (default: 1000)
- `DB_PATH`: SQLite database path (default: `data/training_data.db`)
- `OUTPUT_DIR`: Output directory for exports (default: `output`)

### Model Selection

Models are split automatically:
- First half → Scenario generation
- Second half → Reasoning generation

Example: `MODELS=model1,model2,model3,model4`
- Scenario: `model1, model2`
- Reasoning: `model3, model4`

## Usage

### Generate Training Data

```bash
# Generate 10,000 examples (web UI enabled by default)
python main.py generate --count 10000

# Generate 50,000 examples
python main.py generate --count 50000

# Disable web UI
python main.py generate --count 10000 --no-web
```

**Web UI Features:**
- Auto-refreshes every 5 seconds
- Shows real-time progress (valid/total examples)
- Displays latest generated example preview
- Calculates time remaining based on generation rate
- Provides download links for train/val/test sets (after export)

### Export to Training Format

```bash
# Default split (80/10/10)
python main.py export

# Custom split
python main.py export --train-split 0.85 --val-split 0.1 --test-split 0.05
```

### View Statistics

```bash
python main.py stats
```

## Output Format

Exported files are in LLaMA chat template format:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are Dexter, a crypto trading bot assistant..."
    },
    {
      "role": "user",
      "content": "Market context:\n{...}\n\nWhat should we do?"
    },
    {
      "role": "assistant",
      "content": "<reasoning>\n{...}\n</reasoning>\n\n<decision>\n{...}\n</decision>"
    }
  ]
}
```

Files are written as JSONL:
- `output/train.jsonl` (80% by default)
- `output/val.jsonl` (10% by default)
- `output/test.jsonl` (10% by default)

## Validation Pipeline

1. **Schema Validation**: Pydantic models ensure correct structure
2. **Format Validation**: XML tags, numeric ranges, required fields
3. **Content Validation**: Quality checks (coherence, realism, context matching)

Invalid examples are stored with `validation_status=INVALID` for analysis.

## Performance

- **Throughput**: 10,000+ validated examples per hour (depends on API limits)
- **Validation Rate**: <1% invalid data in final dataset
- **Auto-scaling**: Workers scale based on queue size and rate limits
- **Batch Writes**: SQLite writes batched for performance

## Architecture

```
Scenario Generator (Model 1) → Validation → Queue
    ↓
Reasoning Generator (Model 2) → Multi-stage Validation → SQLite
    ↓
Export → JSONL (LLaMA format) → Train/Val/Test split
```

## License

MIT

