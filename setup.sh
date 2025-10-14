#!/bin/bash

echo "Setting up Voice CAPTCHA System..."

# Update system
sudo apt update

# Install system dependencies
sudo apt install -y python3-pip portaudio19-dev python3-pyaudio wget unzip

# Install Python packages
pip install Flask==2.3.3 Flask-CORS==4.0.0 speechrecognition==3.10.0
pip install scikit-learn==1.3.0 numpy==1.24.3 joblib==1.3.2
pip install selenium==4.12.0 librosa==0.10.1 soundfile==0.12.1 kagglehub==0.1.7

# Install ChromeDriver
echo "Installing ChromeDriver..."
wget -q https://storage.googleapis.com/chrome-for-testing-public/122.0.6261.69/linux64/chromedriver-linux64.zip
unzip -q chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm -rf chromedriver-linux64.zip chromedriver-linux64

echo "Setup complete!"
echo "To start the server: python app.py"
echo "To test: python test_bot_simulation.py"