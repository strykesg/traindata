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

# Configure max file size (10GB for large models)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB

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
    
    # Ensure directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Debug: list all files in directory
    try:
        all_files = list(MODELS_DIR.iterdir())
        print(f"📁 Models directory contents: {[f.name for f in all_files]}")
    except Exception as e:
        print(f"⚠️  Error listing directory: {e}")
    
    # Find all .gguf files
    try:
        gguf_files = list(MODELS_DIR.glob('*.gguf'))
        print(f"📦 Found {len(gguf_files)} .gguf files")
    except Exception as e:
        print(f"⚠️  Error finding .gguf files: {e}")
        gguf_files = []
    
    for model_file in gguf_files:
        try:
            # Skip symlinks that point to current.gguf
            if model_file.name == 'current.gguf' and model_file.is_symlink():
                continue
                
            stat = model_file.stat()
            models.append({
                'name': model_file.name,
                'size': f"{stat.st_size / (1024**3):.2f} GB",
                'size_bytes': stat.st_size,
                'is_active': False  # We're not using current.gguf anymore
            })
        except Exception as e:
            print(f"⚠️  Error processing {model_file.name}: {e}")
            continue
    
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
        # Ensure directory exists
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file.save(str(filepath))
        
        # Verify file was saved
        if not filepath.exists():
            flash(f'Upload failed: File was not saved', 'error')
            return redirect(url_for('index'))
        
        # Get file size
        file_size = filepath.stat().st_size
        flash(f'Model {filename} uploaded successfully! ({file_size / (1024**3):.2f} GB)', 'success')
        
        # Log for debugging
        print(f"✓ Uploaded: {filepath} ({file_size} bytes)")
        
    except Exception as e:
        import traceback
        error_msg = f'Upload failed: {str(e)}'
        print(f"✗ Upload error: {error_msg}")
        print(traceback.format_exc())
        flash(error_msg, 'error')
    
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


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size too large error"""
    return jsonify({'error': 'File too large. Maximum size is 10GB.'}), 413


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

