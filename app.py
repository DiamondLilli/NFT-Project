from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import random
import string
import hashlib
import os
# from datetime import datetime
import numpy as np
from datetime import datetime, timedelta

# Create Flask app first
app = Flask(__name__)
CORS(app)

# Simple dataset loader (no external dependencies)
class SimpleDatasetLoader:
    def __init__(self):
        self.audio_files = []
        self.text_labels = []
        self.use_dataset = False
        
    def download_dataset(self):
        """Simulate dataset download"""
        print("Using simulated dataset (no download required)")
        self.use_dataset = True
        return "/simulated/dataset/path"
    
    def load_audio_samples(self, max_samples=100):
        """Load simulated audio samples"""
        print(f"Generating {max_samples} simulated CAPTCHA samples...")
        
        # Create simulated data
        self.audio_files = []
        self.text_labels = []
        
        for i in range(max_samples):
            # Generate random sequences
            sequence = ''.join(random.choices('0123456789', k=random.randint(3, 6)))
            self.audio_files.append(f"/simulated/audio/audio_{i:03d}.wav")
            self.text_labels.append(sequence)
        
        print(f"Generated {len(self.audio_files)} simulated samples")
        return list(zip(self.audio_files, self.text_labels))
    
    def get_random_captcha(self):
        """Get a random CAPTCHA from simulated dataset"""
        if not self.audio_files:
            self.load_audio_samples(50)
        
        if self.audio_files:
            idx = random.randint(0, len(self.audio_files) - 1)
            return self.audio_files[idx], self.text_labels[idx]
        return None, None

# Initialize dataset loader
dataset_loader = SimpleDatasetLoader()

class EnhancedAudioCaptchaGenerator:
    def __init__(self):
        self.dataset_loader = dataset_loader
        self.use_dataset = False
        
    def initialize_dataset(self):
        """Initialize and download dataset"""
        try:
            self.dataset_loader.download_dataset()
            self.dataset_loader.load_audio_samples()
            self.use_dataset = True
            print("Dataset initialized successfully")
            return True
        except Exception as e:
            print(f"Dataset initialization failed: {e}")
            self.use_dataset = False
            return False
    
    def generate_challenge_from_dataset(self):
        """Generate challenge using real CAPTCHA audio from dataset"""
        if not self.use_dataset:
            return self.generate_synthetic_challenge()
        
        audio_path, true_text = self.dataset_loader.get_random_captcha()
        
        if audio_path and true_text:
            return {
                'type': 'dataset_audio',
                'audio_path': audio_path,
                'true_text': true_text,
                'message': f"Listen to the audio and type what you hear. The sequence has {len(true_text)} digits."
            }
        else:
            return self.generate_synthetic_challenge()
    
    def generate_synthetic_challenge(self):
        """Fallback to synthetic challenge generation"""
        sequence = ''.join(random.choices('0123456789', k=4))
        return {
            'type': 'synthetic',
            'sequence': sequence,
            'message': f"Please speak or type the sequence: {sequence}"
        }

# Initialize enhanced generator
enhanced_generator = EnhancedAudioCaptchaGenerator()
dataset_initialized = enhanced_generator.initialize_dataset()

# Initialize database
def init_db():
    conn = sqlite3.connect('captcha.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS challenges
                 (id TEXT PRIMARY KEY, 
                  sequence TEXT, 
                  created_at TIMESTAMP,
                  attempts INTEGER DEFAULT 0,
                  solved BOOLEAN DEFAULT FALSE,
                  challenge_type TEXT)''')
    conn.commit()
    conn.close()

# Flask Routes - defined AFTER app creation

@app.route('/')
def home():
    return jsonify({
        "message": "Enhanced Voice CAPTCHA Server is running!",
        "dataset_available": dataset_initialized,
        "endpoints": [
            "/api/enhanced/generate-challenge",
            "/api/verify-response", 
            "/api/alternative-challenge",
            "/api/audio/<challenge_id>",
            "/api/status"
        ]
    })

@app.route('/api/text-to-speech/<sequence>')
def text_to_speech(sequence):
    """Generate text-to-speech audio for any sequence"""
    try:
        # In a production system, you would generate actual audio files
        # For now, we'll return a success response indicating TTS capability
        return jsonify({
            'sequence': sequence,
            'audio_available': True,
            'message': f'Audio for sequence {sequence} would be generated via text-to-speech',
            'accessibility_note': 'Browser text-to-speech is used for audio challenges'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
challenge_attempts = {}

@app.route('/api/verify-response', methods=['POST'])
def verify_response():
    data = request.json or {}
    challenge_id = data.get('challenge_id')
    user_response = data.get('response', '')
    ip_address = request.remote_addr
    
    # Basic rate limiting
    now = datetime.now()
    if ip_address in challenge_attempts:
        last_attempt = challenge_attempts[ip_address]
        if now - last_attempt < timedelta(seconds=2):  # 2 second delay
            return jsonify({
                'success': False,
                'message': 'Please wait before trying again',
                'rate_limited': True
            })
    
    challenge_attempts[ip_address] = now
    if not challenge_id:
        return jsonify({'success': False, 'error': 'Missing challenge_id'})
    
    # Get challenge from database
    conn = sqlite3.connect('captcha.db')
    c = conn.cursor()
    c.execute('SELECT sequence, attempts FROM challenges WHERE id = ?', (challenge_id,))
    result = c.fetchone()
    
    if not result:
        return jsonify({'success': False, 'error': 'Invalid challenge'})
    
    sequence, attempts = result
    
    # Update attempts
    c.execute('UPDATE challenges SET attempts = ? WHERE id = ?', (attempts + 1, challenge_id))
    conn.commit()
    
    # Simple verification
    user_clean = ''.join(filter(str.isdigit, str(user_response)))
    sequence_clean = ''.join(filter(str.isdigit, sequence))
    
    success = user_clean == sequence_clean
    
    if success:
        c.execute('UPDATE challenges SET solved = ? WHERE id = ?', (True, challenge_id))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        'success': success,
        'message': 'Access granted' if success else 'Access denied',
        'expected': sequence_clean,
        'provided': user_clean
    })

@app.route('/api/alternative-challenge', methods=['POST'])
def alternative_challenge():
    """Provide alternative challenge method"""
    sequence = ''.join(random.choices('0123456789', k=3))  # Shorter sequence
    challenge_id = hashlib.md5(f"{sequence}{datetime.now()}".encode()).hexdigest()[:16]
    
    conn = sqlite3.connect('captcha.db')
    c = conn.cursor()
    c.execute('INSERT INTO challenges (id, sequence, created_at, challenge_type) VALUES (?, ?, ?, ?)',
              (challenge_id, sequence, datetime.now(), 'alternative'))
    conn.commit()
    conn.close()
    
    return jsonify({
        'challenge_id': challenge_id,
        'sequence': sequence,
        'message': f"Alternative challenge: Please type {sequence}",
        'type': 'alternative_digits',
        'accessibility_note': 'Simplified challenge with shorter sequence'
    })

@app.route('/api/audio/<challenge_id>')
def serve_audio(challenge_id):
    """Serve audio file for dataset challenges"""
    # For now, return a mock response since we don't have real audio files
    # In production, this would serve actual audio files
    
    conn = sqlite3.connect('captcha.db')
    c = conn.cursor()
    c.execute('SELECT sequence, challenge_type FROM challenges WHERE id = ?', (challenge_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'Challenge not found'}), 404
    
    sequence, challenge_type = result
    
    if challenge_type == 'dataset_audio':
        # In a real implementation, you would serve the actual audio file
        # For now, return a mock response
        return jsonify({
            'message': f'Audio challenge for sequence: {sequence}',
            'note': 'In production, this would return the actual audio file',
            'sequence': sequence
        })
    
    return jsonify({'error': 'Audio not available for this challenge type'}), 404

@app.route('/api/status')
def status():
    """Get server status"""
    conn = sqlite3.connect('captcha.db')
    c = conn.cursor()
    
    # Get stats
    c.execute('SELECT COUNT(*) FROM challenges')
    total_challenges = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM challenges WHERE solved = TRUE')
    solved_challenges = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM challenges WHERE challenge_type = "dataset_audio"')
    dataset_challenges = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'status': 'running',
        'dataset_available': dataset_initialized,
        'challenges_generated': total_challenges,
        'challenges_solved': solved_challenges,
        'dataset_challenges_used': dataset_challenges,
        'timestamp': datetime.now().isoformat()
    })
@app.route('/api/enhanced/generate-challenge', methods=['POST'])
def enhanced_generate_challenge():
    """Generate challenge using dataset or synthetic fallback"""
    data = request.json or {}
    use_dataset = data.get('use_dataset', True)
    
    if use_dataset and enhanced_generator.use_dataset:
        challenge = enhanced_generator.generate_challenge_from_dataset()
    else:
        challenge = enhanced_generator.generate_synthetic_challenge()
    
    # Create challenge record
    challenge_text = challenge.get('true_text', challenge.get('sequence', ''))
    challenge_id = hashlib.md5(f"{challenge_text}{datetime.now()}".encode()).hexdigest()[:16]
    
    conn = sqlite3.connect('captcha.db')
    c = conn.cursor()
    c.execute('INSERT INTO challenges (id, sequence, created_at, challenge_type) VALUES (?, ?, ?, ?)',
              (challenge_id, challenge_text, datetime.now(), challenge['type']))
    conn.commit()
    conn.close()
    
    response_data = {
        'challenge_id': challenge_id,
        'challenge_type': challenge['type'],
        'message': challenge['message'],
        'sequence_length': len(challenge_text),
        'audio_support': True,  # EXPLICITLY STATE AUDIO SUPPORT
        'audio_type': 'browser_tts',  # Specify the type of audio support
        'accessible': True
    }
    
    # If using dataset audio, provide the audio file info
    if challenge['type'] == 'dataset_audio':
        response_data['audio_url'] = f'/api/audio/{challenge_id}'
        response_data['audio_type'] = 'pre_recorded'
        response_data['note'] = 'Audio challenge from dataset'
        # Provide a TTS fallback for accessibility: include the sequence so
        # browsers can speak the digits if the pre-recorded audio is not played.
        response_data['sequence'] = challenge_text
    else:
        response_data['note'] = 'Synthetic text challenge with browser text-to-speech'
        response_data['sequence'] = challenge_text  # Include sequence for synthetic
    
    return jsonify(response_data)

# Main execution
if __name__ == '__main__':
    print("🚀 Starting Enhanced Voice CAPTCHA Server...")
    init_db()
    print("✅ Database initialized")
    print("📊 Dataset status:", "Available" if dataset_initialized else "Using synthetic data")
    print("🌐 Server starting on http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET  /              - Server status")
    print("  POST /api/enhanced/generate-challenge - Generate CAPTCHA")
    print("  POST /api/verify-response            - Verify response")
    print("  POST /api/alternative-challenge      - Get simpler challenge")
    print("  GET  /api/status                     - System statistics")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(debug=True, port=5000, host='0.0.0.0')