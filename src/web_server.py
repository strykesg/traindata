"""Simple web server for monitoring training data generation progress."""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from flask import Flask, jsonify, send_file, render_template_string
from threading import Thread

from src.storage.db import TrainingDataDB
from src.config import Config

logger = logging.getLogger(__name__)

# HTML template for the web UI
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Training Data Generator - Progress</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .progress-section {
            margin-bottom: 30px;
        }
        .progress-bar-container {
            background: #e0e0e0;
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-bar {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .time-estimate {
            margin-top: 10px;
            color: #666;
            font-size: 0.9em;
        }
        .latest-example {
            background: #f5f5f5;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .latest-example h3 {
            color: #333;
            margin-bottom: 10px;
        }
        .example-content {
            background: white;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .download-section {
            text-align: center;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 8px;
        }
        .download-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: transform 0.2s;
        }
        .download-btn:hover {
            transform: scale(1.05);
        }
        .download-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-left: 10px;
        }
        .status-running {
            background: #4caf50;
            color: white;
        }
        .status-complete {
            background: #2196f3;
            color: white;
        }
        .refresh-indicator {
            text-align: right;
            color: #999;
            font-size: 0.85em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Training Data Generator <span class="status-badge status-{{ status }}">{{ status_text }}</span></h1>
        <p class="subtitle">Real-time progress monitoring</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ stats.valid }}</div>
                <div class="stat-label">Valid Examples</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">Total Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.invalid }}</div>
                <div class="stat-label">Invalid (Discarded)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ validation_rate }}%</div>
                <div class="stat-label">Validation Rate</div>
            </div>
        </div>
        
        {% if target_count > 0 %}
        <div class="progress-section">
            <h3>Progress: {{ stats.valid }} / {{ target_count }}</h3>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {{ progress_pct }}%">
                    {{ progress_pct }}%
                </div>
            </div>
            {% if time_remaining %}
            <div class="time-estimate">
                ⏱️ Estimated time remaining: {{ time_remaining }}
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if latest_example %}
        <div class="latest-example">
            <h3>Latest Example (ID: {{ latest_example.id }})</h3>
            <div class="example-content">{{ latest_example.content }}</div>
        </div>
        {% endif %}
        
        <div class="download-section">
            {% if can_download %}
            <a href="/download/train.jsonl" class="download-btn">Download Train Set</a>
            <a href="/download/val.jsonl" class="download-btn">Download Val Set</a>
            <a href="/download/test.jsonl" class="download-btn">Download Test Set</a>
            <a href="/download/all" class="download-btn">Download All (ZIP)</a>
            {% else %}
            <button class="download-btn" disabled>Export data first to enable downloads</button>
            {% endif %}
        </div>
        
        <div class="refresh-indicator">
            Last updated: {{ last_updated }} | Auto-refresh: 5s
        </div>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setTimeout(function() {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
"""

class WebServer:
    """Web server for monitoring training data generation."""
    
    def __init__(self, config: Config, db: TrainingDataDB, pipeline: Optional[Any] = None):
        self.config = config
        self.db = db
        self.pipeline = pipeline
        self.target_count = 0
        self.start_time: Optional[datetime] = None
        self.last_stats: Dict[str, Any] = {}
        
        # Create Flask app
        self.app = Flask(__name__)
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching
        
        # Setup routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/api/stats', 'api_stats', self.api_stats)
        self.app.add_url_rule('/api/latest', 'api_latest', self.api_latest)
        self.app.add_url_rule('/download/<filename>', 'download', self.download_file, methods=['GET'])
    
    def set_target_count(self, count: int):
        """Set target count for progress tracking."""
        self.target_count = count
        if self.start_time is None:
            self.start_time = datetime.now()
    
    def index(self):
        """Render main dashboard."""
        stats = self.db.get_stats()
        self.last_stats = stats
        
        # Calculate progress
        progress_pct = 0
        if self.target_count > 0:
            progress_pct = min(100, int((stats['valid'] / self.target_count) * 100))
        
        # Calculate time remaining
        time_remaining = None
        if self.start_time and stats['valid'] > 0 and self.target_count > stats['valid']:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = stats['valid'] / elapsed if elapsed > 0 else 0
            remaining = (self.target_count - stats['valid']) / rate if rate > 0 else 0
            if remaining > 0:
                td = timedelta(seconds=int(remaining))
                hours = td.seconds // 3600
                minutes = (td.seconds % 3600) // 60
                if hours > 0:
                    time_remaining = f"{hours}h {minutes}m"
                else:
                    time_remaining = f"{minutes}m"
        
        # Get latest example
        latest_example = None
        try:
            examples = self.db.get_valid_examples(limit=1)
            if examples:
                ex = examples[0]
                # Format for display
                scenario = ex['scenario']
                reasoning = ex['reasoning']
                content = f"Scenario Type: {scenario.get('scenario_type', 'N/A')}\n"
                content += f"Decision: {scenario.get('decision_prompt', 'N/A')}\n"
                content += f"Reasoning: {reasoning.get('reasoning', 'N/A')[:200]}...\n"
                content += f"Action: {reasoning.get('decision', {}).get('action', 'N/A')}\n"
                content += f"Confidence: {reasoning.get('decision', {}).get('confidence', 0):.2f}"
                
                latest_example = {
                    'id': scenario.get('_metadata', {}).get('scenario_id', 'N/A'),
                    'content': content
                }
        except Exception as e:
            logger.error(f"Error getting latest example: {e}")
        
        # Check if export files exist
        output_dir = Path(self.config.output_dir)
        can_download = (output_dir / "train.jsonl").exists()
        
        # Determine status
        status = "running"
        status_text = "Running"
        if self.target_count > 0 and stats['valid'] >= self.target_count:
            status = "complete"
            status_text = "Complete"
        
        # Validation rate
        validation_rate = 0
        if stats['total'] > 0:
            validation_rate = int((stats['valid'] / stats['total']) * 100)
        
        return render_template_string(
            UI_TEMPLATE,
            stats=stats,
            target_count=self.target_count,
            progress_pct=progress_pct,
            time_remaining=time_remaining,
            latest_example=latest_example,
            can_download=can_download,
            status=status,
            status_text=status_text,
            validation_rate=validation_rate,
            last_updated=datetime.now().strftime("%H:%M:%S")
        )
    
    def api_stats(self):
        """API endpoint for stats."""
        stats = self.db.get_stats()
        return jsonify({
            'stats': stats,
            'target_count': self.target_count,
            'progress_pct': min(100, int((stats['valid'] / self.target_count) * 100)) if self.target_count > 0 else 0,
        })
    
    def api_latest(self):
        """API endpoint for latest example."""
        try:
            examples = self.db.get_valid_examples(limit=1)
            if examples:
                return jsonify(examples[0])
            return jsonify({'error': 'No examples yet'})
        except Exception as e:
            return jsonify({'error': str(e)})
    
    def download_file(self, filename: str):
        """Download file endpoint."""
        output_dir = Path(self.config.output_dir)
        
        if filename == "all":
            # Create ZIP of all files
            import zipfile
            import tempfile
            import os
            
            zip_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            zip_path.close()
            
            with zipfile.ZipFile(zip_path.name, 'w') as zipf:
                for file in ['train.jsonl', 'val.jsonl', 'test.jsonl']:
                    file_path = output_dir / file
                    if file_path.exists():
                        zipf.write(file_path, file)
            
            return send_file(
                zip_path.name,
                mimetype='application/zip',
                as_attachment=True,
                download_name='training_data.zip'
            )
        else:
            file_path = output_dir / filename
            if file_path.exists():
                return send_file(
                    str(file_path),
                    mimetype='application/json',
                    as_attachment=True
                )
            return jsonify({'error': 'File not found'}), 404
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the web server."""
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)


def run_web_server(config: Config, db: TrainingDataDB, pipeline: Optional[Any] = None):
    """Run web server in a separate thread."""
    server = WebServer(config, db, pipeline)
    thread = Thread(target=server.run, args=('0.0.0.0', 5000, False), daemon=True)
    thread.start()
    logger.info("Web server started on http://0.0.0.0:5000")
    return server

