"""
Flask Web Interface
Provides web-based configuration and monitoring for the broadcast audio system
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from threading import Thread, Lock
import time


app = Flask(__name__)
config_lock = Lock()
CONFIG_PATH = 'config.json'

# Global state for audio and decision systems
audio_state = {
    'initialized': False,
    'device_info': {},
    'last_analysis': {},
    'error': None
}

decision_state = {
    'current_camera': 'wide_shot',
    'last_decision': {},
    'history': []
}


def load_config():
    """Load configuration from JSON file"""
    with config_lock:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        return {}


def save_config(config):
    """Save configuration to JSON file"""
    with config_lock:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)


@app.route('/')
def index():
    """Display real-time settings and status"""
    config = load_config()
    
    return render_template('index.html',
                         config=config,
                         audio_state=audio_state,
                         decision_state=decision_state)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Allow editing of thresholds and decision parameters"""
    if request.method == 'POST':
        config = load_config()
        
        # Update thresholds
        if 'volume_threshold' in request.form:
            try:
                config['thresholds']['volume_threshold'] = float(request.form['volume_threshold'])
            except ValueError:
                pass
        
        if 'min_active_frames' in request.form:
            try:
                config['thresholds']['min_active_frames'] = int(request.form['min_active_frames'])
            except ValueError:
                pass
        
        # Update camera settings
        if 'default_camera' in request.form:
            config['cameras']['default_camera'] = request.form['default_camera']
        
        # Update decision settings
        if 'priority_mode' in request.form:
            config['decision']['priority_mode'] = request.form['priority_mode']
        
        if 'idle_timeout_seconds' in request.form:
            try:
                config['decision']['idle_timeout_seconds'] = float(request.form['idle_timeout_seconds'])
            except ValueError:
                pass
        
        # Update audio settings
        if 'sample_rate' in request.form:
            try:
                config['audio']['sample_rate'] = int(request.form['sample_rate'])
            except ValueError:
                pass
        
        if 'chunk_size' in request.form:
            try:
                config['audio']['chunk_size'] = int(request.form['chunk_size'])
            except ValueError:
                pass
        
        if 'channels' in request.form:
            try:
                config['audio']['channels'] = int(request.form['channels'])
            except ValueError:
                pass
        
        save_config(config)
        return redirect(url_for('settings'))
    
    config = load_config()
    return render_template('settings.html', config=config)


@app.route('/api/status')
def api_status():
    """API endpoint to get current system status"""
    config = load_config()
    
    return jsonify({
        'config': config,
        'audio_state': audio_state,
        'decision_state': decision_state,
        'timestamp': time.time()
    })


@app.route('/api/threshold', methods=['POST'])
def api_update_threshold():
    """API endpoint to update volume threshold"""
    data = request.get_json()
    
    if 'volume_threshold' not in data:
        return jsonify({'error': 'volume_threshold required'}), 400
    
    try:
        threshold = float(data['volume_threshold'])
        config = load_config()
        config['thresholds']['volume_threshold'] = threshold
        save_config(config)
        
        return jsonify({'success': True, 'volume_threshold': threshold})
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid threshold value'}), 400


@app.route('/api/camera', methods=['POST'])
def api_update_camera():
    """API endpoint to update default camera"""
    data = request.get_json()
    
    if 'default_camera' not in data:
        return jsonify({'error': 'default_camera required'}), 400
    
    camera = data['default_camera']
    config = load_config()
    config['cameras']['default_camera'] = camera
    save_config(config)
    
    return jsonify({'success': True, 'default_camera': camera})


def update_audio_state(new_state):
    """Update global audio state"""
    audio_state.update(new_state)


def update_decision_state(new_state):
    """Update global decision state"""
    decision_state.update(new_state)
    
    # Keep history of last 50 decisions
    if 'last_decision' in new_state and new_state['last_decision']:
        decision_state['history'].append(new_state['last_decision'])
        if len(decision_state['history']) > 50:
            decision_state['history'].pop(0)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
