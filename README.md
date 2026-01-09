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
export GROQ_API_KEY=your_api_key_here
docker-compose up --build
```

**GPU Server:**
```bash
export GROQ_API_KEY=your_api_key_here
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### Access

Once running, open your browser to:
- **Main Interface:** https://localhost/
- **API Documentation:** http://localhost:8000/docs

## 📁 Project Structure

```
project/
├── frontend/                 # Custom HTML interface
│   ├── index.html           # Main page
│   ├── styles.css           # Professional styling
│   ├── app.js               # Application logic
│   └── audio-player.js      # WaveSurfer wrapper
├── medical_api/             # Backend API
│   ├── api.py               # FastAPI application
│   ├── vibert_service.py    # Punctuation service
│   ├── groq_service.py      # Summarization service
│   └── models/              # ASR & Diarization models
├── vibert_pipeline/         # ViBERT model setup
├── nginx/                   # Nginx configuration
├── certs/                   # SSL certificates
├── docker-compose.yml       # CPU deployment
├── docker-compose.gpu.yml   # GPU extension
└── Dockerfile               # Container image
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

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide (Quick start, Git workflow, Production, Troubleshooting)
- **[BUTTON_DESIGN_SYSTEM.md](BUTTON_DESIGN_SYSTEM.md)** - UI design system and button specifications

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

### Infrastructure
- Docker & Docker Compose
- Nginx (Reverse proxy, SSL/TLS)
- PyTorch (ML framework)
- CUDA (GPU acceleration)

## 🔒 Security

- HTTPS by default with SSL certificates
- CORS properly configured
- File size limits enforced (500MB max)
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

