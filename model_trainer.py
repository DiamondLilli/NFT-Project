# model_trainer.py
import tensorflow as tf
from tensorflow import keras
import numpy as np
import librosa
from sklearn.model_selection import train_test_split
from dataset_loader import dataset_loader

class CaptchaModelTrainer:
    def __init__(self):
        self.model = None
        self.characters = '0123456789abcdefghijklmnopqrstuvwxyz'
        self.max_length = 10
        
    def preprocess_audio_batch(self, audio_files, labels):
        """Preprocess batch of audio files for training"""
        processed_audio = []
        processed_labels = []
        
        for audio_file, label in zip(audio_files, labels):
            try:
                # Preprocess audio
                audio, sr = dataset_loader.preprocess_audio(audio_file)
                if audio is not None:
                    # Extract MFCC features
                    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
                    
                    # Pad or truncate to consistent size
                    if mfccs.shape[1] < 100:
                        mfccs = np.pad(mfccs, ((0, 0), (0, 100 - mfccs.shape[1])))
                    else:
                        mfccs = mfccs[:, :100]
                    
                    processed_audio.append(mfccs)
                    processed_labels.append(label)
                    
            except Exception as e:
                print(f"Error processing {audio_file}: {e}")
                continue
        
        return np.array(processed_audio), processed_labels
    
    def build_model(self, input_shape):
        """Build CNN model for CAPTCHA recognition"""
        model = keras.Sequential([
            # First Conv Block
            keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.BatchNormalization(),
            
            # Second Conv Block
            keras.layers.Conv2D(64, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.BatchNormalization(),
            
            # Third Conv Block
            keras.layers.Conv2D(128, (3, 3), activation='relu'),
            keras.layers.MaxPooling2D((2, 2)),
            keras.layers.BatchNormalization(),
            
            # Global pooling and dense layers
            keras.layers.GlobalAveragePooling2D(),
            keras.layers.Dense(256, activation='relu'),
            keras.layers.Dropout(0.5),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(len(self.characters), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self, epochs=50):
        """Train the model on the CAPTCHA dataset"""
        print("Loading dataset for training...")
        dataset_loader.download_dataset()
        samples = dataset_loader.load_audio_samples(1000)
        
        if not samples:
            print("No samples found for training")
            return False
        
        audio_files, labels = zip(*samples)
        
        print("Preprocessing audio data...")
        X, y = self.preprocess_audio_batch(audio_files, labels)
        
        if len(X) == 0:
            print("No valid training data after preprocessing")
            return False
        
        # Reshape for CNN (add channel dimension)
        X = X[..., np.newaxis]
        
        # Convert labels to numerical format
        y_numeric = [self.characters.index(char) for label in y for char in label[:1]]  # First char only for simplicity
        
        # For now, using first character classification (simplified)
        # In production, you'd want sequence-to-sequence model
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_numeric[:len(X)], test_size=0.2, random_state=42
        )
        
        print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples")
        
        # Build and train model
        self.model = self.build_model(X_train[0].shape)
        
        print("Starting model training...")
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=32,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3)
            ]
        )
        
        # Evaluate model
        test_loss, test_accuracy = self.model.evaluate(X_test, y_test)
        print(f"Test Accuracy: {test_accuracy:.4f}")
        
        # Save model
        self.model.save('captcha_model.h5')
        print("Model saved as 'captcha_model.h5'")
        
        return True

# Usage
if __name__ == "__main__":
    trainer = CaptchaModelTrainer()
    trainer.train_model(epochs=30)