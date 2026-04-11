# Medical ASR System - Vietnamese Speech-to-Text with Diarization (Demo)

Professional **demo** medical transcription system with speaker diarization, punctuation restoration, and AI summarization.

> **Demo only – not for real clinical deployment or production patient data.**

---

## 💡 About the project:

- **Faster documentation**: Turns a Vietnamese doctor–patient conversation audio file into a structured transcript plus short summary.
- **Clear speaker separation**: Automatically labels who is speaking (e.g. doctor vs patient) with timestamps.
- **Higher readability**: Restores punctuation and capitalization so transcripts look like real medical notes, not raw ASR output.
- **End-to-end system**: Shows how I design and ship a complete ML solution: custom web UI → FastAPI backend → ASR + diarization + ViBERT + LLM summarization → Docker/Nginx deployment.

**Example demo workflow:** A 20-minute consultation recording is uploaded → the system produces a diarized, punctuated transcript and an AI-generated summary that could be pasted into an EMR (in a real product).

> This repository is intentionally framed as a **portfolio demo** to demonstrate system design, not a certified medical device.

---

## 🎯 Key Features

- **Vietnamese ASR** – Offline speech recognition using Sherpa-ONNX.
- **Speaker Diarization** – Automatic speaker identification and labeling.
- **Punctuation Restoration** – ViBERT-powered punctuation enhancement for Vietnamese.
- **AI Summarization** – Groq API integration with LLaMA-family models.
- **Professional Web Interface** – Custom HTML/CSS/JavaScript frontend (no low-code framework).
- **Audio Waveform Visualization** – WaveSurfer.js with click-to-seek and auto-pause.
- **Microphone Recording** – Browser-based audio capture.
- **Audio Quality Enhancement** – Noise reduction and volume normalization.
- **SSL/HTTPS via Nginx** – Reverse proxy and HTTPS in the Docker deployment.
- **CPU/GPU Support** – Flexible docker-compose configs for CPU servers and GPU servers.

---

## 🧭 What This Project Demonstrates

- **End-to-end ML system design**
  - Browser frontend, FastAPI backend, audio processing pipeline, and multi-model orchestration.
- **Applied speech + NLP**
  - Using Sherpa-ONNX for ASR, Pyannote for diarization, ViBERT for punctuation, and an LLM for summarization.
- **Production-style engineering**
  - Docker, docker-compose, Nginx reverse proxy, HTTPS, health checks, and resource constraints.
- **Configuration and observability mindset**
  - Centralized `config.py`, health endpoints, logs, and explicit thresholds for different environments.
- **Pragmatic trade-offs**
  - Honest notes about where the system performs best and where it struggles, instead of pretending it is production-ready for hospitals.

---

## 🧪 Demo Flow

1. **Record or upload audio** – A Vietnamese consultation or medical conversation.
2. **Run the pipeline** – The backend processes the file through ASR → diarization → punctuation → summarization.
3. **Review results** – UI displays speaker-labeled transcript with timestamps and an optional AI summary.
4. **Copy output** – In a real system this could be pasted into a medical record; in this demo it is for exploration only.

---

## 🚀 Quick Start

> This section is for **local development / demo only**, not clinical use.

### Option A – Local Dev (CPU, No SSL)

This is the simplest way to explore the backend and API without full Docker + Nginx setup.

1. **Clone the repo and install dependencies** (Python 3.10+ recommended):

```bash
git clone https://github.com/NguyenThuan-data/VI_STT_DIAR_PUNC.git
cd VI_STT_DIAR_PUNC
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2. **Set the Groq API key:**

```bash
export GROQ_API_KEY=your_api_key_here  # PowerShell: $env:GROQ_API_KEY="your_api_key_here"
```

3. **Start the FastAPI backend:**

```bash
uvicorn medical_api.api:app --reload --host 0.0.0.0 --port 8000
```

4. **Test the API quickly:**

- Open `http://localhost:8000/docs` in your browser.
- Use the `/api/health` endpoint to confirm the service is up.
- Use the `/api/transcribe` endpoint to upload a small audio file and see the JSON response.

5. **(Optional) Serve the frontend locally:**

For a very simple static dev setup:

```bash
cd frontend
python -m http.server 3000
```

Then open `http://localhost:3000` and configure the frontend (if needed) so that it calls the API at `http://localhost:8000`.

> In the full Docker setup, Nginx handles this routing and SSL; in dev mode we keep it simple and focus on the core pipeline.

### Option B – Docker Deployment

**Prerequisites**

- Docker & Docker Compose
- Nvidia Docker (for GPU servers only)
- Required models downloaded into `medical_api/models/` (see below)
- SSL certificates in `certs/` directory (self-signed or real)

**CPU Server:**

```bash
cd docker
export GROQ_API_KEY=your_api_key_here
docker-compose up --build
```

**GPU Server:**

```bash
cd docker
export GROQ_API_KEY=your_api_key_here
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

**Access:**

- **Main Interface:** `https://localhost/` (or `http://localhost/` depending on your cert config)
- **API Documentation:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

---

## 📁 Project Structure (Simplified)

```text
project/
├── docker/                   # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.gpu.yml
│   └── start_services.sh
├── frontend/                 # Custom HTML interface
│   ├── index.html           # Main page
│   ├── styles.css           # Professional styling
│   ├── app.js               # Application logic
│   └── audio-player.js      # WaveSurfer wrapper
├── medical_api/             # Backend API
│   ├── api.py               # FastAPI endpoints (thin layer)
│   ├── config.py            # Centralized configuration
│   ├── exceptions.py        # Custom exception types
│   ├── services/            # Business logic layer
│   │   ├── asr_service.py   # ASR & diarization
│   │   ├── audio_processor.py # Pipeline orchestration
│   │   ├── vibert_service.py  # Punctuation restoration
│   │   └── groq_service.py    # AI summarization
│   └── models/              # ML model implementations & cache
├── nginx/                   # Nginx reverse proxy config
├── certs/                   # SSL certificates (not in Git)
├── uploads/                 # Temporary audio files (auto-deleted)
└── docs/                    # Additional documentation & screenshots (optional)
```

---

## 🔍 Models & Capabilities (Demo-Level)

This is a **demo** system with realistic components, not a fully validated clinical product.

### Models

- **ASR:** Sherpa-ONNX Vietnamese model.
- **Diarization:** Pyannote diarization pipeline.
- **Punctuation:** ViBERT-based punctuation model for Vietnamese.
- **Summarization:** Groq-hosted LLaMA-style model (configurable via `groq_service`).

### Works Best For

| Scenario                                | Expected Quality                                  |
|-----------------------------------------|---------------------------------------------------|
| Quiet clinic room, clear voices         | High transcription accuracy, stable diarization   |
| Phone/Zoom with decent microphone       | Good transcription; diarization depends on noise  |
| Single speaker (dictation-style)        | Very strong transcription, simple segmentation    |

### Struggles With

| Scenario                                | Limitations                                       |
|-----------------------------------------|---------------------------------------------------|
| Very noisy environments (ER, cafeteria) | Diarization less reliable, more artifacts         |
| Heavy overlap (people interrupting)     | ASR and diarization both become less stable       |
| Extremely long files (>1 hour)         | Processing time and memory usage increase         |

See `medical_api/config.py` and **AUDIO_QUALITY_GUIDE.md** for tuning thresholds such as `CLUSTERING_THRESHOLD` and noise reduction options.

---

## 🎨 User Interface Highlights

### Audio Input

- **File Upload:** Drag & drop or click to browse (MP3, WAV, M4A, OGG).
- **Microphone Recording:** Direct in-browser recording with a clear timer.
- **Audio Player:** Professional waveform visualization with playback controls.

### Special Audio UX

- **No Scrollbar:** Waveform compressed to fit container width.
- **Click-to-Seek:** Click anywhere on the waveform to jump to that time.
- **Auto-Pause:** Playback automatically pauses after seeking.

### Processing & Output

- **AI Summary:** Optional Groq-powered summarization.
- **Real-time Logs:** Terminal-style processing logs on the page.
- **Status Indicator:** Live API health monitoring.
- **Transcript View:** Speaker-labeled text with timestamps and punctuation.
- **Summary View:** AI-generated medical-style summary (demo only).

---

## 🔧 API Endpoints (Backend)

### Health Check

```bash
GET /api/health
```

### Transcribe Audio

```bash
POST /api/transcribe
Content-Type: multipart/form-data
Body: file (audio file)
```

### Generate Summary

```bash
POST /api/summarize
Content-Type: application/json
Body: {"text": "transcript text"}
```

For more detail, see `http://localhost:8000/docs` when the backend is running.

---

## 📖 Additional Documentation

- **AUDIO_QUALITY_GUIDE.md** – **READ THIS FIRST** for audio quality factors, requirements, and troubleshooting.
- **DEPLOYMENT.md** – Complete deployment guide (Quick start, Git workflow, Production-style setup, Troubleshooting).
- **CHANGELOG.md** – Version history and recent improvements.
- **medical_api/README.md** – Backend architecture documentation.

---

## 🛠️ Technology Stack

### Frontend

- HTML5, CSS3, Vanilla JavaScript.
- WaveSurfer.js for audio visualization.
- Responsive layout for desktop and tablet.

### Backend

- FastAPI (Python web framework).
- Sherpa-ONNX (Vietnamese ASR).
- Pyannote (Speaker diarization).
- ViBERT (Punctuation restoration).
- Groq API (AI summarization).
- Librosa, SoundFile, pydub, noisereduce (Audio processing and enhancement).

### Infrastructure

- Docker & Docker Compose.
- Nginx (Reverse proxy, SSL/TLS termination).
- PyTorch & CUDA (for GPU acceleration in suitable environments).

---

## ⚙️ Configuration Overview

All configuration is centralized in `medical_api/config.py`.

### Example Parameters

```python
# Diarization threshold (0.0-1.0)
# Lower = more speakers, Higher = fewer speakers
DiarizationConfig.CLUSTERING_THRESHOLD = 0.52

# Minimum segment duration (seconds)
# Higher = filter more noise, lower = keep short speech
AudioConfig.MIN_SEGMENT_DURATION = 1.0

# Audio preprocessing
AudioConfig.ENABLE_NOISE_REDUCTION = True  # Reduce background noise
AudioConfig.ENABLE_NORMALIZATION = True    # Normalize volume
AudioConfig.ENABLE_DEBUG_LOGGING = False   # Detailed logs
```

### Scenario Presets

See **AUDIO_QUALITY_GUIDE.md** for suggestions, for example:

- Studio recording: `CLUSTERING_THRESHOLD = 0.50`
- Phone/Zoom: `CLUSTERING_THRESHOLD = 0.48`
- Single speaker: `CLUSTERING_THRESHOLD = 0.65`
- Noisy environment: `CLUSTERING_THRESHOLD = 0.60`

---

## 🔒 Demo, Compliance & Data Privacy

- This is a **demo repository** and is **not** a certified medical device or production system.
- Do **not** use with real patient-identifiable data without proper legal, ethical, and compliance review.
- HTTPS and basic security measures (file size limits, temp file cleanup, CORS) are included to simulate a production-style deployment, but they are **not a complete security review**.

---

## 🐛 Troubleshooting (Summary)

### API Status Shows "Offline"

```bash
# Check containers
docker ps

# View logs
docker logs medical_asr_system

# Restart
docker-compose restart
```

### Models Not Loading

```bash
# Verify models exist
ls -la medical_api/models/

# Check permissions
chmod -R 755 medical_api/models/
```

### GPU Not Detected

```bash
# Ensure using GPU compose file
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build

# Verify nvidia-docker
nvidia-docker --version
```

See **DEPLOYMENT.md** for deeper troubleshooting.

---

## 🙏 Acknowledgments

- **Sherpa-ONNX** – Offline ASR engine.
- **Pyannote** – Speaker diarization.
- **ViBERT** – Vietnamese punctuation model.
- **Groq** – Fast AI inference.
- **WaveSurfer.js** – Audio visualization.

---

**Version:** 2.0 (Custom HTML Frontend – Demo)  \
**Last Updated:** 2026-03-17
