# Frontend Migration: Gradio → Custom HTML

## Overview

This document details the complete replacement of the Gradio-based interface with a professional custom HTML/CSS/JavaScript frontend. The new interface provides better control, professional styling, and specific features like click-to-seek audio playback with automatic pause.

---

## Table of Contents

1. [Architecture Changes](#architecture-changes)
2. [New File Structure](#new-file-structure)
3. [Key Features](#key-features)
4. [API Endpoints](#api-endpoints)
5. [Deployment Guide](#deployment-guide)
6. [Feature Comparison](#feature-comparison)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Changes

### Before (Gradio-based)

```
User Browser → Gradio (Port 7860) → Python Backend → ASR API (Port 8000)
                  ↓
            ViBERT + Groq Processing
```

**Issues:**
- Two Python processes running (Gradio + API)
- Limited UI customization
- Gradio dependencies and complexity

### After (Custom HTML)

```
User Browser → Nginx (Port 443 HTTPS)
                  ↓
             Static HTML/CSS/JS
                  ↓
           FastAPI Backend (Port 8000)
                  ↓
        ASR + ViBERT + Groq (All in one service)
```

**Benefits:**
- Single Python process (simplified architecture)
- Professional, customizable UI
- Better performance and control
- Click-to-seek with pause feature
- No scrollbar in waveform (compressed view)

---

## New File Structure

### Frontend Files (New)

```
frontend/
├── index.html          # Main interface page
├── styles.css          # Professional styling
├── app.js              # Application logic and API integration
└── audio-player.js     # WaveSurfer.js wrapper with custom controls
```

### Backend Services (New)

```
medical_api/
├── api.py              # Main FastAPI app (updated with CORS & new endpoints)
├── vibert_service.py   # ViBERT punctuation service (NEW)
└── groq_service.py     # Groq summarization service (NEW)
```

### Configuration Files (Modified)

```
docker-compose.yml      # Updated: removed port 7860, added frontend volume
docker-compose.gpu.yml  # NEW: GPU extension for GPU servers
Dockerfile              # Updated: copy frontend files
start_services.sh       # Updated: removed Gradio startup
nginx/nginx.conf        # Updated: serve static files + proxy API
requirements.txt        # Updated: removed Gradio
```

---

## Key Features

### 1. Audio Waveform Visualization

**Technology:** WaveSurfer.js v7.7.3

**Configuration:**
```javascript
WaveSurfer.create({
    container: '#waveform',
    waveColor: '#4A90E2',
    progressColor: '#2E5C8A',
    height: 128,
    normalize: true,
    scrollParent: false,      // ✓ No scrollbar
    minPxPerSec: 1,           // ✓ Compressed waveform
    fillParent: true,         // ✓ Fits container width
    autoCenter: false,        // ✓ No auto-scrolling
    interact: true            // ✓ Click-to-seek enabled
});
```

**Click-to-Seek & Pause:**
- Click anywhere on waveform
- Audio jumps to that timestamp
- **Playback automatically pauses**
- User must manually click play to resume

### 2. File Upload

**Features:**
- Drag & drop support
- Click to browse
- File type validation (audio files only)
- Size validation (max 500MB)
- Visual feedback on drag-over

**Supported Formats:** MP3, WAV, M4A, OGG, WebM

### 3. Microphone Recording

**Features:**
- Browser-based recording (MediaRecorder API)
- Visual recording indicator with pulse animation
- Real-time timer display
- Stop button to finish recording
- Automatically loads recorded audio into player

### 4. Processing Options

**AI Summary Checkbox:**
- Optional Groq API integration
- Uses LLaMA 3.3 70B (with fallback models)
- Automatic chunking for long transcripts

### 5. Results Display

**Transcript:**
- Speaker labels (Speaker_0, Speaker_1, etc.)
- Timestamps in HH:MM:SS format
- ViBERT-enhanced punctuation
- Copy to clipboard button

**Summary:**
- AI-generated medical summary
- Model used indicator
- Copy to clipboard button

**System Logs:**
- Real-time processing logs
- Terminal-style display
- Auto-scroll to latest

---

## API Endpoints

### Base URL
```
https://your-domain.com/api/
```

### 1. Health Check

**Endpoint:** `GET /api/health`

**Response:**
```json
{
    "status": "healthy",
    "service": "medical-asr-api",
    "models_loaded": true,
    "vibert_available": true,
    "groq_available": true
}
```

### 2. Transcribe Audio

**Endpoint:** `POST /api/transcribe`

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (audio file)

**Response:**
```json
{
    "status": "success",
    "text": "[00:00:05] Speaker_0: Xin chào bác sĩ.\n[00:00:08] Speaker_1: Chào bạn...",
    "segments": [
        {
            "start": 5.2,
            "end": 7.8,
            "speaker": "Speaker_0",
            "text": "Xin chào bác sĩ."
        }
    ],
    "processing_time": 23.45
}
```

### 3. Generate Summary

**Endpoint:** `POST /api/summarize`

**Request:**
```json
{
    "text": "Full transcript text here..."
}
```

**Response:**
```json
{
    "status": "success",
    "summary": "Patient presented with...",
    "model_used": "llama-3.3-70b-versatile"
}
```

---

## Deployment Guide

### Requirements

**Software:**
- Docker & Docker Compose
- Nvidia Docker (GPU servers only)

**Files to Copy:**
- Entire project folder (code + frontend)
- `medical_api/models/` directory (trained models)
- `certs/` directory (SSL certificates)

### Deployment Commands

#### CPU-Only Server

```bash
# 1. Set environment variable
export GROQ_API_KEY=your_api_key_here

# 2. Build and run
docker-compose up --build
```

#### GPU Server

```bash
# 1. Set environment variable
export GROQ_API_KEY=your_api_key_here

# 2. Build and run with GPU support
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### Access Points

- **Frontend:** https://localhost/ (or your domain)
- **API Docs:** http://localhost:8000/docs
- **Direct API:** http://localhost:8000/health

### Port Configuration

- **80:** HTTP (redirects to HTTPS)
- **443:** HTTPS (Nginx serves frontend)
- **8000:** FastAPI backend (internal, proxied by Nginx)

---

## Feature Comparison

| Feature | Gradio | Custom HTML | Notes |
|---------|--------|-------------|-------|
| **UI Customization** | Limited | Full | Complete control over design |
| **File Upload** | ✓ | ✓ | Improved drag & drop |
| **Microphone Recording** | ✓ | ✓ | Better visual feedback |
| **Audio Playback** | Basic | Advanced | WaveSurfer with click-to-seek-pause |
| **Waveform Display** | Simple | Professional | Compressed view, no scrollbar |
| **Click-to-Seek** | ✗ | ✓ | Jump to timestamp + auto-pause |
| **AI Summary** | ✓ | ✓ | Same Groq integration |
| **Speaker Diarization** | ✓ | ✓ | Same Sherpa-ONNX backend |
| **Punctuation** | ✓ | ✓ | Same ViBERT model |
| **Real-time Logs** | Limited | Enhanced | Terminal-style display |
| **Copy Results** | Manual | One-click | Copy buttons added |
| **Mobile Responsive** | Partial | Full | Optimized for all devices |
| **SSL/HTTPS** | Manual | Automatic | Nginx handles certificates |
| **Performance** | 2 processes | 1 process | Simpler architecture |
| **Deployment** | Complex | Simple | Single Docker command |

---

## Technical Details

### Frontend Stack

- **HTML5** - Semantic markup
- **CSS3** - Custom styling with CSS variables
- **Vanilla JavaScript** - No framework dependencies
- **WaveSurfer.js** - Audio waveform visualization

### Backend Stack

- **FastAPI** - Modern Python web framework
- **Sherpa-ONNX** - Vietnamese ASR
- **Pyannote** - Speaker diarization
- **ViBERT** - Punctuation restoration
- **Groq API** - AI summarization (LLaMA models)

### Browser Compatibility

- **Chrome/Edge:** Full support
- **Firefox:** Full support
- **Safari:** Full support (iOS 14.5+)
- **Opera:** Full support

**Required Features:**
- MediaRecorder API (for microphone)
- Fetch API (for AJAX calls)
- ES6+ JavaScript support

---

## Troubleshooting

### Issue: API Status shows "Offline"

**Possible Causes:**
1. Backend container not running
2. CORS configuration issue
3. Network connectivity

**Solutions:**
```bash
# Check container status
docker ps

# View backend logs
docker logs medical_asr_system

# Restart containers
docker-compose restart
```

### Issue: Waveform not displaying

**Possible Causes:**
1. Audio file format not supported
2. File corrupted
3. Browser compatibility

**Solutions:**
- Try converting audio to MP3 or WAV
- Check browser console for errors
- Ensure WaveSurfer.js CDN is accessible

### Issue: Click-to-seek not pausing

**Check:**
- Browser console for JavaScript errors
- WaveSurfer.js properly initialized
- Event listeners attached

### Issue: Summary not generating

**Possible Causes:**
1. GROQ_API_KEY not set
2. Rate limit exceeded
3. Network timeout

**Solutions:**
```bash
# Set API key
export GROQ_API_KEY=your_key

# Rebuild container
docker-compose down
docker-compose up --build

# Check logs for rate limit messages
docker logs medical_asr_system | grep -i "rate"
```

### Issue: GPU not being used

**Verification:**
```bash
# Check if using GPU compose file
docker-compose config

# Verify nvidia-docker installed
nvidia-docker --version

# Check GPU visibility inside container
docker exec medical_asr_system nvidia-smi
```

**Solution:**
Ensure using GPU compose override:
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### Issue: Models not loading

**Possible Causes:**
1. Model files not copied to server
2. Volume mounts incorrect
3. Permissions issue

**Solutions:**
```bash
# Verify model files exist
ls -la medical_api/models/

# Check volume mounts
docker inspect medical_asr_system | grep -A 10 Mounts

# Fix permissions
chmod -R 755 medical_api/models/
```

---

## Migration Checklist

When moving to a new server:

- [ ] Copy entire project folder
- [ ] Copy `medical_api/models/` directory
- [ ] Copy `certs/` directory (SSL certificates)
- [ ] Set `GROQ_API_KEY` environment variable
- [ ] Choose CPU or GPU deployment command
- [ ] Run `docker-compose up --build`
- [ ] Access https://your-domain/
- [ ] Test file upload
- [ ] Test microphone recording
- [ ] Test click-to-seek-pause feature
- [ ] Test transcription
- [ ] Test AI summary generation
- [ ] Verify waveform has no scrollbar

---

## Performance Notes

### Frontend
- Gzip compression enabled
- Static files cached by browser
- CDN for WaveSurfer.js
- Optimized CSS with variables

### Backend
- Single Python process (reduced memory)
- CORS properly configured
- Long timeouts for large files (600s)
- Efficient audio processing pipeline

### Network
- HTTPS by default
- 500MB max file upload
- WebSocket support (future-ready)
- Proper proxy headers

---

## Future Enhancements

Potential improvements for future versions:

1. **Authentication** - Add user login system
2. **File Management** - Browse/delete saved transcripts
3. **Real-time Transcription** - Stream processing
4. **Multi-language** - Support other languages
5. **Custom Models** - Allow model switching
6. **Export Formats** - PDF, DOCX, SRT subtitles
7. **Collaboration** - Share transcripts with team
8. **Analytics** - Usage statistics dashboard

---

## Support

For issues or questions:
1. Check this documentation
2. Review Docker logs: `docker logs medical_asr_system`
3. Check browser console for frontend errors
4. Verify API endpoints with `/docs`

---

## Summary

The new custom HTML frontend provides:
- ✅ Professional, medical-themed UI
- ✅ Click-to-seek with automatic pause
- ✅ Compressed waveform (no scrollbar)
- ✅ Simplified deployment (CPU/GPU support)
- ✅ Single command deployment
- ✅ Better performance
- ✅ Full customization control

**Deployment remains simple:** Copy files → Set API key → Run Docker command → Done!

