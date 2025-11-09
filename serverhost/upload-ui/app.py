#!/usr/bin/env python3
"""
Model Upload and Management UI for llama.cpp server
"""
import os
import sys
import requests
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configure max file size (10GB for large models)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for debugging

MODELS_DIR = Path(os.environ.get('MODELS_DIR', '/app/models'))
LLAMA_SERVER_URL = os.environ.get('LLAMA_SERVER_URL', 'http://llama-server:8080')
ALLOWED_EXTENSIONS = {'gguf'}


def initialize_models_directory():
    """Initialize models directory on startup"""
    print(f"\n{'='*60}")
    print("Upload UI Initialization")
    print(f"{'='*60}")
    
    # Ensure directory exists
    try:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✓ Models directory ensured: {MODELS_DIR}")
    except Exception as e:
        print(f"✗ Failed to create models directory: {e}")
        sys.exit(1)
    
    # Check write permissions
    if not os.access(MODELS_DIR, os.W_OK):
        print(f"✗ Models directory is not writable: {MODELS_DIR}")
        sys.exit(1)
    print(f"✓ Models directory is writable")
    
    # List existing models
    try:
        existing_models = list(MODELS_DIR.glob('*.gguf'))
        print(f"✓ Found {len(existing_models)} existing model(s):")
        for model in existing_models:
            size = model.stat().st_size
            print(f"  - {model.name} ({size / (1024**3):.2f} GB)")
    except Exception as e:
        print(f"⚠️  Error listing models: {e}")
    
    # Check for symlinks (old current.gguf)
    current_link = MODELS_DIR / 'current.gguf'
    if current_link.exists() or current_link.is_symlink():
        print(f"⚠️  Found old current.gguf symlink (will be ignored)")
    
    print(f"{'='*60}\n")


# Initialize on import
initialize_models_directory()


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
    # Re-verify models directory on each request (ensures persistence)
    try:
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"⚠️  Warning: Could not ensure models directory: {e}")
    
    models = get_models()
    server_healthy = check_llama_server_health()
    
    # Log model count for debugging
    print(f"📊 Serving index page with {len(models)} models")
    
    return render_template('index.html', 
                         models=models, 
                         server_healthy=server_healthy,
                         llama_url=LLAMA_SERVER_URL.replace('llama-server', 'localhost'))


@app.route('/upload', methods=['POST'])
def upload_model():
    """Upload a new model"""
    print(f"\n{'='*50}")
    print("UPLOAD REQUEST RECEIVED")
    print(f"{'='*50}")
    print(f"MODELS_DIR: {MODELS_DIR}")
    print(f"MODELS_DIR exists: {MODELS_DIR.exists()}")
    print(f"MODELS_DIR is writable: {os.access(MODELS_DIR, os.W_OK)}")
    
    if 'file' not in request.files:
        print("✗ No file in request.files")
        flash('No file provided', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    print(f"File object: {file}")
    print(f"File filename: {file.filename}")
    print(f"File content_type: {file.content_type}")
    
    if file.filename == '':
        print("✗ Empty filename")
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        print(f"✗ Invalid file type: {file.filename}")
        flash('Only .gguf files are allowed', 'error')
        return redirect(url_for('index'))
    
    filename = secure_filename(file.filename)
    filepath = MODELS_DIR / filename
    
    # Resolve any symlinks to get the actual path
    try:
        resolved_path = filepath.resolve()
        print(f"Secure filename: {filename}")
        print(f"Target path: {filepath}")
        print(f"Resolved path: {resolved_path}")
    except Exception as e:
        print(f"Could not resolve path: {e}")
        resolved_path = filepath
    
    sys.stdout.flush()
    
    # Check if file already exists
    if filepath.exists():
        existing_size = filepath.stat().st_size
        print(f"⚠️  File already exists: {existing_size} bytes")
        flash(f'Model {filename} already exists', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Ensure directory exists
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory ensured: {MODELS_DIR}")
        
        # Get file size before saving
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        print(f"File size: {file_size} bytes ({file_size / (1024**3):.2f} GB)")
        sys.stdout.flush()
        
        # Save file - use Flask's save method which handles FileStorage correctly
        print(f"Saving to: {filepath}")
        print(f"Starting save operation...")
        sys.stdout.flush()
        
        try:
            # CRITICAL: Ensure directory exists RIGHT before saving
            # This handles any race conditions or permission issues
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Verify directory is actually writable by trying to create a test file
            test_file = MODELS_DIR / '.write_test'
            try:
                test_file.touch()
                test_file.unlink()
                print(f"✓ Directory write test passed")
            except Exception as test_error:
                print(f"✗ Directory write test failed: {test_error}")
                raise Exception(f"Cannot write to directory {MODELS_DIR}: {test_error}")
            
            sys.stdout.flush()
            
            # Reset file pointer to beginning
            file.seek(0)
            
            # Use Flask's save method (handles FileStorage correctly)
            # This should complete before we continue
            print(f"Calling file.save() to: {filepath}")
            print(f"Directory exists: {MODELS_DIR.exists()}")
            print(f"Directory is writable: {os.access(MODELS_DIR, os.W_OK)}")
            sys.stdout.flush()
            
            # Get absolute path to ensure no path issues
            try:
                # Try to resolve (works if parent exists)
                absolute_filepath = filepath.resolve()
            except (OSError, RuntimeError):
                # If resolve fails, use absolute() which always works
                absolute_filepath = filepath.absolute()
            print(f"Using absolute path: {absolute_filepath}")
            print(f"Parent directory: {absolute_filepath.parent}")
            print(f"Parent exists: {absolute_filepath.parent.exists()}")
            sys.stdout.flush()
            
            # Save the file - Flask's save method
            try:
                # Use absolute path string
                file.save(str(absolute_filepath))
                print(f"✓ file.save() returned")
                sys.stdout.flush()
            except (FileNotFoundError, OSError) as save_error:
                # If Flask's save fails, try manual write as fallback
                print(f"⚠️  Flask save failed ({type(save_error).__name__}), trying manual write: {save_error}")
                sys.stdout.flush()
                
                # Ensure parent directory exists
                absolute_filepath.parent.mkdir(parents=True, exist_ok=True)
                
                # Manual write fallback
                with open(absolute_filepath, 'wb') as f:
                    file.seek(0)
                    written = 0
                    while True:
                        chunk = file.read(1024 * 1024)  # 1MB chunks
                        if not chunk:
                            break
                        f.write(chunk)
                        written += len(chunk)
                        # Log progress every 100MB
                        if written % (100 * 1024 * 1024) == 0:
                            print(f"  Manual write progress: {written / (1024**3):.2f} GB")
                            sys.stdout.flush()
                    f.flush()
                    os.fsync(f.fileno())
                print(f"✓ Manual write completed: {written} bytes")
                sys.stdout.flush()
                
                # Update filepath reference for rest of function
                filepath = absolute_filepath
            else:
                # Flask save succeeded, use absolute path for consistency
                filepath = absolute_filepath
            
            # Wait for file to be written (for large files, this may take time)
            import time
            max_wait = 300  # 5 minutes max wait
            wait_interval = 1  # Check every second
            waited = 0
            
            print(f"Waiting for file at: {filepath}")
            sys.stdout.flush()
            
            while waited < max_wait:
                if filepath.exists():
                    current_size = filepath.stat().st_size
                    if current_size >= file_size:
                        print(f"✓ File fully written: {current_size} bytes")
                        sys.stdout.flush()
                        break
                    else:
                        print(f"⏳ File writing in progress: {current_size}/{file_size} bytes ({current_size*100/file_size:.1f}%)")
                        sys.stdout.flush()
                else:
                    print(f"⏳ Waiting for file to appear... ({waited}s)")
                    sys.stdout.flush()
                
                time.sleep(wait_interval)
                waited += wait_interval
            
            # Final verification
            if not filepath.exists():
                print(f"✗ File does not exist after save and wait!")
                sys.stdout.flush()
                flash(f'Upload failed: File was not saved', 'error')
                return redirect(url_for('index'))
            
            final_size = filepath.stat().st_size
            if final_size < file_size:
                print(f"✗ File incomplete after wait: {final_size}/{file_size} bytes")
                sys.stdout.flush()
                filepath.unlink()
                flash(f'Upload failed: File incomplete ({final_size} of {file_size} bytes)', 'error')
                return redirect(url_for('index'))
            
            print(f"✓ File exists and is complete after save")
            sys.stdout.flush()
            
            # Ensure file is written to disk
            try:
                fd = os.open(str(filepath), os.O_RDONLY)
                os.fsync(fd)
                os.close(fd)
                print(f"✓ File synced to disk")
                sys.stdout.flush()
            except Exception as sync_error:
                print(f"⚠️  Could not sync file (non-critical): {sync_error}")
                sys.stdout.flush()
            
        except Exception as save_error:
            import traceback
            print(f"✗ Save error occurred:")
            print(traceback.format_exc())
            sys.stdout.flush()
            # Clean up partial file on error
            if filepath.exists():
                try:
                    filepath.unlink()
                    print(f"✗ Removed partial file due to error")
                    sys.stdout.flush()
                except:
                    pass
            raise save_error
        
        # Verify file was saved
        if not filepath.exists():
            print(f"✗ File does not exist after save!")
            flash(f'Upload failed: File was not saved', 'error')
            return redirect(url_for('index'))
        
        # Get actual saved file size
        saved_size = filepath.stat().st_size
        print(f"✓ File saved successfully!")
        print(f"  Path: {filepath}")
        print(f"  Size: {saved_size} bytes ({saved_size / (1024**3):.2f} GB)")
        print(f"  Expected: {file_size} bytes")
        
        if saved_size != file_size:
            print(f"⚠️  Size mismatch! Expected {file_size}, got {saved_size}")
            if saved_size < file_size:
                print(f"⚠️  File appears incomplete!")
                filepath.unlink()
                flash(f'Upload failed: File incomplete ({saved_size} of {file_size} bytes)', 'error')
                return redirect(url_for('index'))
        
        # Verify file is readable
        if not os.access(filepath, os.R_OK):
            print(f"⚠️  File is not readable!")
        
        # Set proper permissions
        os.chmod(filepath, 0o644)
        
        print(f"✓ File permissions set: {oct(filepath.stat().st_mode)}")
        sys.stdout.flush()
        
        flash(f'Model {filename} uploaded successfully! ({saved_size / (1024**3):.2f} GB)', 'success')
        
    except Exception as e:
        import traceback
        error_msg = f'Upload failed: {str(e)}'
        print(f"✗ Upload error: {error_msg}")
        print(traceback.format_exc())
        flash(error_msg, 'error')
    
    print(f"{'='*50}\n")
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
    models = get_models()
    print(f"API: Returning {len(models)} models")
    return jsonify({'models': models})


@app.route('/api/verify/<model_name>')
def verify_model(model_name):
    """Verify if a model file exists"""
    model_path = MODELS_DIR / secure_filename(model_name)
    exists = model_path.exists()
    info = {}
    if exists:
        stat = model_path.stat()
        info = {
            'exists': True,
            'size': stat.st_size,
            'size_gb': f"{stat.st_size / (1024**3):.2f}",
            'readable': os.access(model_path, os.R_OK)
        }
    else:
        info = {'exists': False}
    
    return jsonify(info)


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

