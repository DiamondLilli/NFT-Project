# NFT-Project — Voice CAPTCHA Demo

This project implements an accessible voice CAPTCHA demo with a Flask backend and a small frontend. The repository includes a simulated dataset loader and a simplified model trainer.

Contents
- `app.py` — Flask backend (runs on port 5000)
- `serve.py` — static file server for the frontend (runs on port 8000)
- `index.html` — frontend UI that talks to the backend
- `model_trainer.py` — prototype trainer (requires TensorFlow for real training)
- `dataset_loader.py` — simulated dataset helper
- `testing.py` — script that runs evaluation-style checks against the backend
- `requirements.txt` — Python dependencies
- `run_project.py` — automation script to check environment and start backend+frontend

Quick start (Windows - cmd.exe)
1. Open cmd.exe and change to the project folder:
```
cd "C:\Users\Ankita\Documents\Reference books,notes\W26-sem5\NFT\NFT-Project"
```

2. (Optional but recommended) Create and activate a virtual environment:
```
python -m venv .venv
.venv\Scripts\activate
```

3. Install requirements (optional — you can also let `run_project.py` try to install):
```
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
Notes: On Windows, some packages like `PyAudio` or `librosa` may require prebuilt wheels or Visual C++ Build Tools. If `pip install PyAudio` fails, download a matching wheel for your Python version and install it with `pip install <wheel-file>`.

4. Start the project using the automation script (recommended):
```
python run_project.py
```
Options:
- `--install` — have the script attempt to install `requirements.txt` into the current Python environment before starting
- `--create-venv` — create a `.venv` folder (won't activate it)
- `--no-frontend` — start only the backend

5. Open the frontend in your browser:
- Frontend: http://localhost:8000
- Backend API: http://localhost:5000 (for health: `/api/status`)

Run backend or frontend manually
- Backend only:
```
python app.py
```
- Frontend only:
```
python serve.py
```

Testing
- To run the included evaluation script (make sure backend is running):
```
python testing.py
```

Training notes
- `model_trainer.py` uses TensorFlow and librosa. TensorFlow is not included in `requirements.txt` because it's large and platform-specific. If you want to train the model, install TensorFlow separately (CPU version):
```
pip install tensorflow
```
Then run:
```
python model_trainer.py
```

Troubleshooting
- Port in use: if port 5000 or 8000 is occupied, stop the other service or change the port in `app.py`/`serve.py`.
- PyAudio install fails: use a prebuilt wheel matching your Python version or install Visual C++ Build Tools.
- CORS/file access: serve the frontend with `serve.py` rather than opening `index.html` directly so API calls from the browser work.

