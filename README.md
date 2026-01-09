# Medical ASR System - Vietnamese Speech-to-Text with Diarization

Professional medical transcription system with speaker diarization, punctuation restoration, and AI summarization.

## 🎯 Features

- **Vietnamese ASR** - Offline speech recognition using Sherpa-ONNX
- **Speaker Diarization** - Automatic speaker identification and labeling
- **Punctuation Restoration** - ViBERT-powered punctuation enhancement
- **AI Summarization** - Groq API integration with LLaMA models
- **Professional Web Interface** - Custom HTML/CSS/JavaScript frontend
- **Audio Waveform Visualization** - WaveSurfer.js with click-to-seek-pause
- **Microphone Recording** - Browser-based audio capture
- **Audio Quality Enhancement** - Noise reduction and volume normalization
- **SSL/HTTPS** - Secure by default with Nginx
- **CPU/GPU Support** - Flexible deployment options

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Nvidia Docker (GPU servers only)
- Models in `medical_api/models/` directory
- SSL certificates in `certs/` directory

### Deployment

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

### Access

Once running, open your browser to:
- **Main Interface:** https://localhost/ (or http://localhost/)
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 📁 Project Structure

```
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
│   └── models/              # ML model implementations
│       └── vibert/          # ViBERT model & cache
├── nginx/                   # Nginx reverse proxy config
├── certs/                   # SSL certificates (not in Git)
├── uploads/                 # Temporary audio files (auto-deleted)
```

## 🎨 User Interface Features

### Audio Input
- **File Upload:** Drag & drop or click to browse (supports MP3, WAV, M4A, OGG)
- **Microphone Recording:** Record directly from browser with visual timer
- **Audio Player:** Professional waveform visualization with playback controls

### Special Audio Features
- **No Scrollbar:** Waveform compressed to fit container width
- **Click-to-Seek:** Click anywhere on waveform to jump to that time
- **Auto-Pause:** Playback automatically pauses after seeking

### Processing Options
- **AI Summary:** Optional Groq-powered summarization
- **Real-time Logs:** Terminal-style processing logs
- **Status Indicator:** Live API health monitoring

### Results Display
- **Transcript:** Speaker-labeled text with timestamps and punctuation
- **Summary:** AI-generated medical summary (when enabled)
- **Copy Buttons:** One-click copy to clipboard

## 🔧 API Endpoints

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

## 📖 Documentation

- **[AUDIO_QUALITY_GUIDE.md](AUDIO_QUALITY_GUIDE.md)** - 📚 **READ THIS FIRST** - Factors affecting quality, requirements, troubleshooting
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide (Quick start, Git workflow, Production, Troubleshooting)
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and recent improvements
- **[medical_api/README.md](medical_api/README.md)** - Backend architecture documentation

## 🛠️ Technology Stack

### Frontend
- HTML5, CSS3, Vanilla JavaScript
- WaveSurfer.js for audio visualization
- Responsive design for all devices

### Backend
- FastAPI (Python web framework)
- Sherpa-ONNX (Vietnamese ASR)
- Pyannote (Speaker diarization)
- ViBERT (Punctuation restoration)
- Groq API (AI summarization)
- Librosa (Audio processing)
- noisereduce (Noise reduction preprocessing)

### Infrastructure
- Docker & Docker Compose
- Nginx (Reverse proxy, SSL/TLS)
- PyTorch (ML framework)
- CUDA (GPU acceleration)

## ⚙️ Configuration

All configuration is centralized in `medical_api/config.py`:

### Key Parameters
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
See **[AUDIO_QUALITY_GUIDE.md](AUDIO_QUALITY_GUIDE.md)** for:
- Studio recording: `CLUSTERING_THRESHOLD = 0.50`
- Phone/Zoom: `CLUSTERING_THRESHOLD = 0.48`
- Single speaker: `CLUSTERING_THRESHOLD = 0.65`
- Noisy environment: `CLUSTERING_THRESHOLD = 0.60`

## 🔒 Security

- HTTPS by default with SSL certificates
- CORS properly configured
- File size limits enforced (500MB max)
- Temporary files auto-deleted after processing
- Secure API communication

## 📊 Performance

- Single Python process architecture
- Gzip compression enabled
- Efficient audio processing pipeline
- Long timeout support for large files (600s)
- GPU acceleration when available

## 🐛 Troubleshooting

### API Status shows "Offline"
```bash
# Check containers
docker ps

# View logs
docker logs medical_asr_system

# Restart
docker-compose restart
```

### Models not loading
```bash
# Verify models exist
ls -la medical_api/models/

# Check permissions
chmod -R 755 medical_api/models/
```

### GPU not detected
```bash
# Ensure using GPU compose file
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build

# Verify nvidia-docker
nvidia-docker --version
```

For more troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)

## 🚢 Deployment to Production Server

1. **Copy files to server:**
```bash
scp -r project_folder/ user@server:/path/to/destination/
```

2. **SSH and deploy:**
```bash
ssh user@server
cd /path/to/destination/project_folder
export GROQ_API_KEY=your_key
docker-compose up -d --build
```

The `-d` flag runs in background (detached mode).

## 📝 Environment Variables

- `GROQ_API_KEY` - Required for AI summarization
- `USE_GPU` - Automatically set by compose files (true/false)
- `MODEL_DIR` - Model directory path (default: /app/models)

## 🎯 Use Case

**Target:** Medical consultation rooms

**Workflow:**
1. Record doctor-patient conversation
2. Upload audio to system
3. System produces:
   - Time-stamped transcript with speaker identification
   - Proper punctuation and capitalization
   - AI-generated consultation summary
4. Save for medical records

## 🤝 Contributing

This is a production medical system. For modifications:
1. Test thoroughly in development environment
2. Verify HIPAA compliance if handling real patient data
3. Update documentation for any changes
4. Test both CPU and GPU deployments

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- **Sherpa-ONNX** - Offline ASR engine
- **Pyannote** - Speaker diarization
- **ViBERT** - Vietnamese punctuation model
- **Groq** - Fast AI inference
- **WaveSurfer.js** - Audio visualization

## 📞 Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment and troubleshooting
2. Review logs: `docker logs medical_asr_system`
3. Verify API at `/docs` endpoint
4. Check browser console (F12) for frontend errors

---

**Version:** 2.0 (Custom HTML Frontend)  
**Last Updated:** 2026-01-07

