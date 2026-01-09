# Changelog - Medical ASR System

## Version 2.1 - Audio Quality Improvements (January 2025)

### 🎯 Major Improvements

#### 1. Enhanced Audio Preprocessing
- **Noise Reduction**: Automatic background noise removal for better diarization
- **Volume Normalization**: Consistent audio levels for improved transcription
- **Silence Trimming**: Removes leading/trailing silence automatically

#### 2. Improved Speaker Diarization
- **Lower Threshold**: Changed from 0.55 → 0.52 for better speaker separation
- **Segment Merging**: Automatically merges adjacent same-speaker segments (fixes over-segmentation)
- **Better Filtering**: Increased MIN_SEGMENT_DURATION from 0.5s → 1.0s to filter noise

#### 3. Debug & Diagnostics
- **Debug Logging**: Detailed diarization output showing raw segments and speaker distribution
- **Problem Detection**: Helps identify over/under-segmentation issues
- **Enable with**: `AudioConfig.ENABLE_DEBUG_LOGGING = True`

#### 4. Configuration Presets
Added scenario-based recommendations:
- Studio quality: 0.50 threshold
- Phone/Zoom: 0.48 threshold
- Single speaker: 0.65 threshold
- Noisy environment: 0.60 threshold

#### 5. Comprehensive Documentation
- **AUDIO_QUALITY_GUIDE.md**: Complete guide on factors affecting quality
  - Audio recording requirements
  - Environment best practices
  - Troubleshooting common issues
  - Configuration presets
  - Model behavior explanation

### 🔧 Configuration Changes

```python
# medical_api/config.py

class AudioConfig:
    MIN_SEGMENT_DURATION = 1.0  # Increased from 0.5
    ENABLE_NOISE_REDUCTION = True  # NEW
    ENABLE_NORMALIZATION = True  # NEW
    ENABLE_DEBUG_LOGGING = False  # NEW

class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.52  # Decreased from 0.55
    MERGE_GAP_THRESHOLD = 1.0  # NEW - merge segments < 1s apart
```

### 📦 New Dependencies
```
noisereduce>=3.0.0  # Audio noise reduction library
```

### 🐛 Bug Fixes
- Fixed over-segmentation (1 person → 3 speakers) with microphone recordings
- Improved under-segmentation (2 people → 1 speaker) with better threshold
- Better handling of noisy environments and phone/Zoom recordings

### 📝 Files Changed
- `medical_api/config.py`: Enhanced configuration with new parameters
- `medical_api/services/audio_processor.py`: Added preprocessing and segment merging
- `AUDIO_QUALITY_GUIDE.md`: New comprehensive quality documentation
- `requirements.txt`: Added noisereduce library
- `CHANGELOG.md`: This file

### 🎓 What to Read
1. **AUDIO_QUALITY_GUIDE.md** - Understand quality factors and requirements
2. **medical_api/config.py** - See all configuration options and presets
3. **README.md** - Updated deployment and usage instructions

---

## Version 2.0 - Clean Architecture Refactoring (January 2025)

### 🏗️ Architecture Improvements
- Separated concerns into layers (API, Service, Model, Config)
- Created dedicated services for ASR, audio processing, ViBERT, and Groq
- Centralized configuration management
- Custom exception hierarchy
- 100% documentation coverage with Google-style docstrings

### 📁 New Structure
```
medical_api/
├── api.py                    # Thin API layer
├── config.py                 # Centralized configuration
├── exceptions.py             # Custom exceptions
├── services/
│   ├── asr_service.py       # ASR & diarization
│   ├── audio_processor.py   # Pipeline orchestration
│   ├── vibert_service.py    # Punctuation restoration
│   └── groq_service.py      # AI summarization
└── models/
    └── vibert/              # ViBERT model implementation

docker/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.gpu.yml
└── start_services.sh
```

### 🔧 Features
- Speaker ID remapping (sequential numbering)
- Batch ViBERT processing for better performance
- Min segment duration filtering (removes noise)
- GPU/CPU automatic fallback
- Comprehensive error handling

---

## Version 1.0 - Custom Frontend (January 2025)

### 🎨 Frontend Changes
- Replaced Gradio with custom HTML/CSS/JavaScript interface
- Two-column layout (audio left, transcript right)
- WaveSurfer.js integration for waveform visualization
- Time jump feature (hour:minute:second inputs)
- Download transcript and summary as .txt files
- Vietnamese localization
- Custom theme colors (green base, yellow buttons)

### 🚀 Deployment
- Docker-based deployment with CPU/GPU support
- Nginx reverse proxy for static files and API
- CORS enabled for frontend-backend communication
- Health check endpoints
- Production-ready configuration

---

**For complete deployment instructions, see DEPLOYMENT.md**  
**For API documentation, visit /docs after starting the server**

