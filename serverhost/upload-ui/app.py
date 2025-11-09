#!/usr/bin/env python3
"""
Model Upload and Management UI for llama.cpp server
"""
import os
import requests
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

MODELS_DIR = Path(os.environ.get('MODELS_DIR', '/app/models'))
LLAMA_SERVER_URL = os.environ.get('LLAMA_SERVER_URL', 'http://llama-server:8080')
ALLOWED_EXTENSIONS = {'gguf'}

MODELS_DIR.mkdir(exist_ok=True)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_models():
    """Get list of available models"""
    models = []
    for model_file in MODELS_DIR.glob('*.gguf'):
        stat = model_file.stat()
        models.append({
            'name': model_file.name,
            'size': f"{stat.st_size / (1024**3):.2f} GB",
            'size_bytes': stat.st_size,
            'is_active': model_file.name == 'current.gguf' or 
                        (MODELS_DIR / 'current.gguf').resolve() == model_file.resolve()
        })
    return sorted(models, key=lambda x: x['name'])


def check_llama_server_health():
    """Check if llama-server is healthy"""
    try:
        response = requests.get(f"{LLAMA_SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


@app.route('/')
def index():
    """Main page - model management"""
    models = get_models()
    server_healthy = check_llama_server_health()
    return render_template('index.html', 
                         models=models, 
                         server_healthy=server_healthy,
                         llama_url=LLAMA_SERVER_URL.replace('llama-server', 'localhost'))


@app.route('/upload', methods=['POST'])
def upload_model():
    """Upload a new model"""
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Only .gguf files are allowed', 'error')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    filepath = MODELS_DIR / filename
    
    # Check if file already exists
    if filepath.exists():
        flash(f'Model {filename} already exists', 'warning')
        return redirect(url_for('index'))
    
    try:
        file.save(str(filepath))
        flash(f'Model {filename} uploaded successfully!', 'success')
    except Exception as e:
        flash(f'Upload failed: {str(e)}', 'error')
    
    return redirect(url_for('index'))


@app.route('/activate/<model_name>', methods=['POST'])
def activate_model(model_name):
    """Set a model as the active one"""
    model_path = MODELS_DIR / secure_filename(model_name)
    current_link = MODELS_DIR / 'current.gguf'
    
    if not model_path.exists():
        return jsonify({'error': 'Model not found'}), 404
    
    try:
        # Remove old symlink/file
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        
        # Create symlink to new model
        current_link.symlink_to(model_path.name)
        
        # Save active model state for persistence across redeploys
        state_file = MODELS_DIR / '.active_model'
        with open(state_file, 'w') as f:
            f.write(model_path.name)
        
        return jsonify({
            'success': True,
            'message': f'Model {model_name} activated. Restart llama-server to use it.',
            'restart_required': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete/<model_name>', methods=['POST'])
def delete_model(model_name):
    """Delete a model"""
    model_path = MODELS_DIR / secure_filename(model_name)
    
    if not model_path.exists():
        return jsonify({'error': 'Model not found'}), 404
    
    # Don't delete if it's the active model
    current_link = MODELS_DIR / 'current.gguf'
    if current_link.exists() and current_link.resolve() == model_path.resolve():
        return jsonify({'error': 'Cannot delete active model'}), 400
    
    try:
        model_path.unlink()
        return jsonify({'success': True, 'message': f'Model {model_name} deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/models')
def api_models():
    """API endpoint for model list"""
    return jsonify({'models': get_models()})


@app.route('/api/server/status')
def api_server_status():
    """API endpoint for server status"""
    healthy = check_llama_server_health()
    return jsonify({
        'healthy': healthy,
        'url': LLAMA_SERVER_URL
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

