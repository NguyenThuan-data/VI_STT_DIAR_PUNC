# Quick Deployment Guide

## Prerequisites

1. **Docker & Docker Compose** installed
2. **Nvidia Docker** (only for GPU servers)
3. **Models** in `medical_api/models/` directory
4. **SSL Certificates** in `certs/` directory

## Step-by-Step Deployment

### 1. Set Environment Variable

```bash
export GROQ_API_KEY=your_groq_api_key_here
```

To make it permanent, add to `.env` file:
```bash
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

### 2. Choose Deployment Type

#### Option A: CPU Server (Default)

```bash
docker-compose up --build
```

#### Option B: GPU Server

```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### 3. Access the System

Once running, access the system at:
- **Main Interface:** https://localhost/
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Quick Test

1. Open browser to https://localhost/
2. Upload an audio file or record from microphone
3. Check the "Generate AI Summary" checkbox
4. Click "Process Transcription"
5. Wait for results
6. Test click-to-seek: Click anywhere on the waveform (should pause)

## Stopping the System

```bash
docker-compose down
```

## Viewing Logs

```bash
# All logs
docker-compose logs -f

# API logs only
docker logs medical_asr_system -f

# Nginx logs only
docker logs medical_asr_nginx -f
```

## Common Issues

### 1. Port Already in Use

If ports 80, 443, or 8000 are already in use:

```bash
# Find what's using the port
sudo lsof -i :443

# Stop existing containers
docker-compose down

# Or change ports in docker-compose.yml
```

### 2. Models Not Found

Ensure your models are in the correct location:
```
medical_api/models/
├── vi_offline/
│   ├── encoder-epoch-20-avg-10.int8.onnx
│   ├── decoder-epoch-20-avg-10.int8.onnx
│   ├── joiner-epoch-20-avg-10.int8.onnx
│   └── tokens.txt
├── dia_seg/
│   └── model.onnx
└── dia_embed/
    └── model.onnx
```

### 3. SSL Certificate Error

If you see certificate warnings:
- Use self-signed certificates (browser will warn, but you can proceed)
- Or use Let's Encrypt for production

## Production Deployment

For production deployment on a remote server:

1. **Copy files to server:**
```bash
scp -r project_folder/ user@server:/path/to/destination/
```

2. **SSH into server:**
```bash
ssh user@server
cd /path/to/destination/project_folder
```

3. **Set API key:**
```bash
export GROQ_API_KEY=your_key
```

4. **Run:**
```bash
# CPU server
docker-compose up -d --build

# GPU server
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

The `-d` flag runs containers in detached mode (background).

## Updating the System

To update after making changes:

```bash
# Stop containers
docker-compose down

# Rebuild and start
docker-compose up --build

# Or for GPU
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

## File Structure

```
project/
├── frontend/                 # NEW: Custom HTML interface
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── audio-player.js
├── medical_api/
│   ├── api.py               # UPDATED: CORS + new endpoints
│   ├── vibert_service.py    # NEW: ViBERT integration
│   ├── groq_service.py      # NEW: Groq integration
│   └── models/              # Your trained models (REQUIRED)
├── vibert_pipeline/
│   └── ...
├── nginx/
│   └── nginx.conf           # UPDATED: Serve frontend + proxy API
├── certs/                   # SSL certificates (REQUIRED)
│   ├── fullchain.pem
│   └── privkey.pem
├── docker-compose.yml       # UPDATED: CPU config
├── docker-compose.gpu.yml   # NEW: GPU extension
├── Dockerfile               # UPDATED: Copy frontend
├── start_services.sh        # UPDATED: API only
├── requirements.txt         # UPDATED: No Gradio
├── FRONTEND_CHANGES.md      # Full documentation
└── DEPLOYMENT_GUIDE.md      # This file
```

## Success Indicators

✅ Docker containers running: `docker ps` shows 2 containers  
✅ API health check: `curl http://localhost:8000/health` returns JSON  
✅ Frontend loads: https://localhost/ shows the interface  
✅ Status indicator: Shows "API Online - Ready" in green  
✅ Audio player: Upload works and shows waveform without scrollbar  
✅ Click-to-seek: Clicking waveform pauses playback  

## Support

For detailed information, see [FRONTEND_CHANGES.md](FRONTEND_CHANGES.md)

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify models exist
3. Check browser console (F12)
4. Ensure GROQ_API_KEY is set

