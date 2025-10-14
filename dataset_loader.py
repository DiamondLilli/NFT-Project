import random
import os

class SimpleDatasetLoader:
    def __init__(self):
        self.audio_files = []
        self.text_labels = []
        self.use_dataset = False
        
    def download_dataset(self):
        """Simulate dataset download - no external dependencies"""
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
    
    def preprocess_audio(self, audio_path, target_sr=16000):
        """Simulate audio preprocessing"""
        # Return dummy data for testing
        import numpy as np
        return np.random.random(16000), target_sr

# Global instance
dataset_loader = SimpleDatasetLoader()