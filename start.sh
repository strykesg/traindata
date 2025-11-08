#!/bin/bash
# Startup script that checks if target is already reached

cd /app

# Load config and check current stats
python3 << EOF
import sys
sys.path.insert(0, '/app')
from src.storage.db import TrainingDataDB
from src.config import Config
import os

try:
    config = Config.from_env()
    db = TrainingDataDB(config.db_path)
    stats = db.get_stats()
    target = int(os.getenv('TARGET_COUNT', '10'))
    
    print(f"Current valid examples: {stats['valid']}")
    print(f"Target: {target}")
    
    if stats['valid'] >= target:
        print(f"✓ Target already reached ({stats['valid']}/{target}). Skipping generation.")
        sys.exit(0)
    else:
        print(f"Need {target - stats['valid']} more examples. Starting generation...")
        sys.exit(1)
except Exception as e:
    print(f"Error checking stats: {e}")
    # If error, proceed with generation
    sys.exit(1)
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    # Target reached, just start web server
    echo "Starting web server only..."
    python3 main.py serve || python3 -c "from src.web_server import WebServer; from src.config import Config; from src.storage.db import TrainingDataDB; import os; os.chdir('/app'); config = Config.from_env(); db = TrainingDataDB(config.db_path); server = WebServer(config, db); server.run(host='0.0.0.0', port=5000)"
else
    # Need to generate, run normal command
    python3 main.py generate --count ${TARGET_COUNT:-10}
fi

