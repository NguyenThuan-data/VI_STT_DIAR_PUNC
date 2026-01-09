# Deployment Guide - Medical ASR System

Complete deployment guide for Vietnamese Medical ASR system with speaker diarization, punctuation restoration, and AI summarization.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [First-Time Deployment](#first-time-deployment)
4. [Git-Based Deployment](#git-based-deployment)
5. [Production Deployment](#production-deployment)
6. [Updating the System](#updating-the-system)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### CPU Server (Default)

```bash
export GROQ_API_KEY=your_groq_api_key_here
docker-compose up --build
```

### GPU Server

```bash
export GROQ_API_KEY=your_groq_api_key_here
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### Access

- **Main Interface:** https://localhost/
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Prerequisites

### Required Software

1. **Docker & Docker Compose** - Container runtime
2. **Nvidia Docker** - Only for GPU servers (Linux only)
3. **Git** - For version control and updates

### Required Files

Before deploying, ensure these directories exist with proper content:

```
project/
├── medical_api/models/      # ASR & Diarization models (REQUIRED)
│   ├── vi_offline/
│   │   ├── encoder-epoch-20-avg-10.int8.onnx
│   │   ├── decoder-epoch-20-avg-10.int8.onnx
│   │   ├── joiner-epoch-20-avg-10.int8.onnx
│   │   └── tokens.txt
│   ├── dia_seg/
│   │   └── model.onnx
│   └── dia_embed/
│       └── model.onnx
├── certs/                   # SSL certificates (REQUIRED)
│   ├── fullchain.pem
│   └── privkey.pem
└── .env                     # Environment variables (OPTIONAL)
```

### Environment Variables

Create a `.env` file (optional) or export variables:

```bash
# Required for AI summarization
GROQ_API_KEY=your_groq_api_key_here

# Automatically set by docker-compose files
USE_GPU=false  # or true for GPU
```

---

## First-Time Deployment

### Step 1: Prepare Models

Models are large files (500MB+) and should NOT be in Git. Copy them manually:

**Option A: From local machine**
```bash
scp -r /path/to/models/ user@server:/path/to/medical-asr/medical_api/
```

**Option B: From shared storage**
```bash
cp -r /shared/models/ ./medical_api/
```

### Step 2: Prepare SSL Certificates

```bash
# Option 1: Self-signed certificates (development)
python generate_cert.py

# Option 2: Copy existing certificates
mkdir -p certs/
cp /path/to/fullchain.pem certs/
cp /path/to/privkey.pem certs/
chmod 600 certs/*.pem
```

### Step 3: Set API Key

```bash
# Method 1: Export (temporary)
export GROQ_API_KEY=your_key

# Method 2: .env file (permanent)
echo "GROQ_API_KEY=your_key" > .env
```

### Step 4: Deploy

**CPU Server:**
```bash
docker-compose up --build
```

**GPU Server:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### Step 5: Verify

```bash
# Check containers running
docker ps

# Should show 2 containers:
# - medical_asr_system (API)
# - medical_asr_nginx (Web server)

# Check API health
curl http://localhost:8000/health

# Access frontend
# Open browser to https://localhost/
```

---

## Git-Based Deployment

### What Goes in Git

✅ **Commit to Git (Code & Config):**
- `frontend/` - HTML, CSS, JavaScript
- `medical_api/*.py` - Python source code
- `vibert_pipeline/*.py` - Python source files
- `nginx/nginx.conf` - Configuration
- `docker-compose*.yml` - Deployment configs
- `Dockerfile` - Build instructions
- `requirements.txt` - Dependencies
- `*.md` - Documentation

❌ **DO NOT Commit (Machine-Specific/Large Files):**
- `medical_api/models/` - Too large (500MB+)
- `vibert_pipeline/vibert_cache/` - Auto-downloaded
- `certs/` - Security-sensitive
- `.env` - Contains API keys
- `__pycache__/` - Python cache
- `saved_transcripts/` - Generated outputs

### Deployment Workflow

#### Scenario 1: Development Machine → GitHub

```bash
# 1. Initialize git (if not already)
git init

# 2. Add all code files
git add frontend/ medical_api/*.py vibert_pipeline/*.py
git add nginx/ docker-compose*.yml Dockerfile
git add requirements.txt *.md .gitignore

# 3. Commit
git commit -m "Update medical ASR system"

# 4. Push to GitHub
git remote add origin https://github.com/your-username/medical-asr.git
git push -u origin main
```

#### Scenario 2: GitHub → New Server

```bash
# 1. Clone repository
git clone https://github.com/your-username/medical-asr.git
cd medical-asr

# 2. Copy models manually (not in Git)
scp -r /source/models/ ./medical_api/

# 3. Copy SSL certificates
cp /source/certs/* ./certs/

# 4. Set API key
export GROQ_API_KEY=your_key

# 5. Deploy
docker-compose up --build
```

#### Scenario 3: Existing Server (Update Code)

**Your current setup - machine has cache and Docker already built:**

```bash
# 1. Navigate to project
cd /path/to/medical-asr

# 2. Stash local changes (if any)
git stash save "Local changes before update"

# 3. Pull latest code
git pull origin main

# 4. Cache files are preserved (not in Git)
# ✓ vibert_pipeline/vibert_cache/  <- Still there
# ✓ medical_api/models/            <- Still there
# ✓ certs/                         <- Still there

# 5. Rebuild and restart
docker-compose down
docker-compose up --build

# 6. Restore local changes if needed
git stash list
git stash pop  # If you want them back
```

### Update Workflows

**If only frontend changed:**
```bash
git pull
# No rebuild needed - Nginx serves from volume
docker-compose restart nginx
```

**If backend code changed:**
```bash
git pull
docker-compose build asr_app
docker-compose restart asr_app
```

**If Docker config changed:**
```bash
git pull
docker-compose down
docker-compose up --build
```

---

## Production Deployment

### Remote Server Deployment

#### Step 1: Copy Files to Server

```bash
# Copy entire project folder
scp -r project_folder/ user@server:/path/to/destination/
```

#### Step 2: SSH and Setup

```bash
# SSH into server
ssh user@server
cd /path/to/destination/project_folder

# Set API key
export GROQ_API_KEY=your_key
```

#### Step 3: Deploy

**CPU Server:**
```bash
docker-compose up -d --build
```

**GPU Server:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

**Note:** The `-d` flag runs containers in detached mode (background).

### Production Best Practices

1. **Use Real SSL Certificates**
   - Let's Encrypt for free certificates
   - Or use organizational certificates

2. **Set Up Monitoring**
   ```bash
   # View logs
   docker-compose logs -f
   
   # Check resource usage
   docker stats
   ```

3. **Configure Backups**
   ```bash
   # Backup transcripts periodically
   tar -czf backup_$(date +%Y%m%d).tar.gz saved_transcripts/
   ```

4. **Firewall Configuration**
   ```bash
   # Allow only HTTPS
   ufw allow 443/tcp
   ufw allow 80/tcp  # For HTTP→HTTPS redirect
   ufw enable
   ```

---

## Updating the System

### Stop Containers

```bash
docker-compose down
```

### View Logs

```bash
# All logs
docker-compose logs -f

# API logs only
docker logs medical_asr_system -f

# Nginx logs only
docker logs medical_asr_nginx -f
```

### Restart Containers

```bash
docker-compose restart
```

### Rebuild After Changes

```bash
docker-compose down
docker-compose up --build
```

### Clean Up Old Images

```bash
# Remove unused containers
docker system prune

# Remove old images
docker image prune
```

---

## Troubleshooting

### 1. API Status Shows "Offline"

**Symptoms:** Frontend shows "API not available"

**Solutions:**
```bash
# Check container status
docker ps

# View backend logs
docker logs medical_asr_system

# Restart containers
docker-compose restart

# If that doesn't work, rebuild
docker-compose down
docker-compose up --build
```

### 2. Port Already in Use

**Symptoms:** Error binding to ports 80, 443, or 8000

**Solutions:**
```bash
# Find what's using the port
sudo lsof -i :443

# Stop existing containers
docker-compose down

# Kill process using port
sudo kill -9 <PID>

# Or change ports in docker-compose.yml
```

### 3. Models Not Found

**Symptoms:** Error loading models on startup

**Solutions:**
```bash
# Verify models exist
ls -la medical_api/models/

# Check directory structure
tree medical_api/models/

# Fix permissions
chmod -R 755 medical_api/models/
```

### 4. SSL Certificate Error

**Symptoms:** Browser shows certificate warning

**Solutions:**
- Self-signed certificates will always warn (safe to proceed in development)
- For production, use Let's Encrypt:
  ```bash
  # Install certbot
  sudo apt install certbot
  
  # Get certificate
  sudo certbot certonly --standalone -d your-domain.com
  
  # Copy to certs folder
  cp /etc/letsencrypt/live/your-domain.com/fullchain.pem certs/
  cp /etc/letsencrypt/live/your-domain.com/privkey.pem certs/
  ```

### 5. GPU Not Being Used

**Symptoms:** System falls back to CPU despite having GPU

**Solutions:**
```bash
# Verify using GPU compose file
docker-compose config

# Check nvidia-docker installed
nvidia-docker --version

# Check GPU visibility
docker exec medical_asr_system nvidia-smi

# Ensure using correct command
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

### 6. ViBERT/Groq Not Available

**Symptoms:** Health check shows service unavailable

**For ViBERT:**
```bash
# Check cache downloaded
ls -la vibert_pipeline/vibert_cache/

# Run setup manually
docker exec medical_asr_system python vibert_pipeline/1_setup_models.py
```

**For Groq:**
```bash
# Verify API key set
echo $GROQ_API_KEY

# Check logs for API errors
docker logs medical_asr_system | grep -i groq
```

### 7. Frontend Not Loading

**Symptoms:** Blank page or 404 errors

**Solutions:**
```bash
# Check Nginx logs
docker logs medical_asr_nginx

# Verify frontend files exist
ls -la frontend/

# Restart Nginx
docker-compose restart nginx

# Clear browser cache (Ctrl+Shift+R)
```

### 8. Transcription Fails

**Symptoms:** Error during processing

**Check:**
1. **File format:** Ensure audio is MP3, WAV, M4A, or OGG
2. **File size:** Must be under 500MB
3. **Backend logs:**
   ```bash
   docker logs medical_asr_system -f
   ```
4. **Memory:** Ensure sufficient RAM/VRAM

### 9. Container Won't Start

**Symptoms:** Container exits immediately

**Solutions:**
```bash
# Check detailed logs
docker-compose logs asr_app

# Verify all required files exist
ls medical_api/models/
ls certs/

# Check for syntax errors
docker-compose config

# Try building without cache
docker-compose build --no-cache
```

---

## Common Issues Reference

| Issue | Quick Fix |
|-------|-----------|
| API offline | `docker-compose restart` |
| Port conflict | `docker-compose down` then check ports |
| Models not found | Verify `medical_api/models/` exists |
| GPU not used | Use GPU compose file |
| Certificate warning | Normal for self-signed, proceed anyway |
| Frontend blank | Clear browser cache (Ctrl+Shift+R) |
| Slow transcription | Check CPU/RAM usage with `docker stats` |
| Summary fails | Verify `GROQ_API_KEY` is set |

---

## Success Indicators

After deployment, verify these:

✅ **Containers Running:** `docker ps` shows 2 containers  
✅ **API Health:** `curl http://localhost:8000/health` returns JSON  
✅ **Frontend Loads:** https://localhost/ shows interface  
✅ **Status Indicator:** Shows "API Online - Ready" (green)  
✅ **File Upload:** Can upload and see waveform  
✅ **No Scrollbar:** Waveform fits container width  
✅ **Click-to-Seek:** Clicking waveform pauses playback  

---

## Performance Optimization

### For Large Files

- Increase timeout in `nginx/nginx.conf` if needed
- Ensure sufficient RAM (8GB+ recommended)
- Use GPU for faster processing

### For Multiple Users

- Scale containers:
  ```bash
  docker-compose up --scale asr_app=3
  ```
- Consider load balancer for production

### Storage Management

```bash
# Clean up old uploads (automatically deleted after processing)
docker exec medical_asr_system du -sh /app/uploads/

# Clean up saved transcripts
rm -rf saved_transcripts/*
```

---

## Next Steps After Deployment

1. **Test All Features:**
   - Upload audio file
   - Record from microphone
   - Click waveform to seek
   - Verify auto-pause works
   - Test AI summary generation
   - Try copy buttons

2. **Configure for Production:**
   - Use real SSL certificates
   - Set up monitoring
   - Configure backups
   - Document server details

3. **Train Your Team:**
   - Share access URL
   - Demonstrate features
   - Provide user guide

---

## Support

For additional help:

1. **Check Logs:** `docker-compose logs -f`
2. **Review README.md:** Main project documentation
3. **Check Browser Console:** Press F12 for frontend errors
4. **Verify API:** Visit http://localhost:8000/docs

---

## Summary

**Deployment is simple:**

1. Copy files + models + certificates to server
2. Set `GROQ_API_KEY` environment variable
3. Run one Docker command (CPU or GPU)
4. Access https://your-server/

**Update is simple:**

1. `git pull origin main`
2. `docker-compose down && docker-compose up --build`

Models and certificates are preserved across updates! 🎉

