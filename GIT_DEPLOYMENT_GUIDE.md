# Git-Based Deployment Guide

## Overview

This guide explains how to use Git to deploy the Medical ASR system to multiple machines, including machines that already have cache files or Docker images built.

---

## 📦 What Goes in Git vs What Doesn't

### ✅ Commit to Git (Code & Configuration)

```
✓ frontend/              # HTML, CSS, JS
✓ medical_api/*.py       # Python source code
✓ vibert_pipeline/*.py   # Python source code
✓ nginx/nginx.conf       # Configuration
✓ docker-compose.yml     # Deployment config
✓ docker-compose.gpu.yml # GPU config
✓ Dockerfile             # Build instructions
✓ start_services.sh      # Startup script
✓ requirements.txt       # Dependencies
✓ *.md                   # Documentation
✓ .gitignore             # Git ignore rules
```

### ❌ DO NOT Commit (Machine-Specific/Large Files)

```
✗ medical_api/models/           # Too large (500MB+)
✗ vibert_pipeline/vibert_cache/ # Auto-downloaded
✗ certs/                        # Security-sensitive
✗ saved_transcripts/            # Generated outputs
✗ .env                          # Sensitive API keys
✗ __pycache__/                  # Python cache
✗ processing_workspace/         # Temp files
```

---

## 🚀 Deployment Workflow

### Scenario 1: First Machine (Development) → GitHub

```bash
# 1. Initialize git (if not already)
git init

# 2. Add .gitignore (already created)
git add .gitignore

# 3. Add code files
git add frontend/
git add medical_api/*.py
git add vibert_pipeline/*.py
git add nginx/
git add docker-compose*.yml
git add Dockerfile
git add start_services.sh
git add requirements.txt
git add *.md

# 4. Commit
git commit -m "Replace Gradio with custom HTML frontend"

# 5. Add remote and push
git remote add origin https://github.com/your-username/medical-asr.git
git branch -M main
git push -u origin main
```

### Scenario 2: New Machine (Fresh Install)

```bash
# 1. Clone repository
git clone https://github.com/your-username/medical-asr.git
cd medical-asr

# 2. Copy models manually (one-time setup)
# Option A: From local machine
scp -r /path/to/models/ user@newserver:/path/to/medical-asr/medical_api/

# Option B: From shared storage/NAS
cp -r /shared/models/ ./medical_api/

# 3. Copy SSL certificates
cp /path/to/certs/ ./certs/

# 4. Set environment variable
export GROQ_API_KEY=your_key

# 5. Deploy
docker-compose up --build
```

### Scenario 3: Existing Machine (Has Cache/Docker Already)

**Your specific case - machine already has cache and Docker built**

```bash
# 1. Navigate to project directory
cd /path/to/medical-asr

# 2. Stash or backup any local changes you want to keep
git stash save "Local changes before update"

# 3. Pull latest code from GitHub
git pull origin main

# 4. Cache files are preserved (not in git)
# ✓ vibert_pipeline/vibert_cache/  <- Still there
# ✓ medical_api/models/            <- Still there
# ✓ certs/                         <- Still there

# 5. Rebuild Docker image (uses cache when possible)
docker-compose build

# 6. Restart containers
docker-compose down
docker-compose up -d

# 7. If you had local changes, review them
git stash list
git stash pop  # If you want to restore them
```

---

## 🔄 Update Workflow (After Git Pull)

### If Only Frontend Changed

```bash
git pull
# No Docker rebuild needed - Nginx serves static files from volume
docker-compose restart nginx
```

### If Backend Code Changed

```bash
git pull
docker-compose build asr_app
docker-compose restart asr_app
```

### If Docker Config Changed

```bash
git pull
docker-compose down
docker-compose up --build
```

---

## 💾 Handling Models & Large Files

### Option 1: Manual Copy (Recommended for Internal Deployment)

**Models stay out of Git, copied manually:**

```bash
# On development machine
tar -czf models.tar.gz medical_api/models/

# Transfer to server
scp models.tar.gz user@server:/tmp/

# On server
cd /path/to/medical-asr
tar -xzf /tmp/models.tar.gz
```

### Option 2: Git LFS (For Team Collaboration)

**If you want models in Git (requires Git LFS):**

```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "*.onnx"
git lfs track "*.bin"
git lfs track "medical_api/models/**"

# Add .gitattributes
git add .gitattributes

# Commit and push (will use LFS for large files)
git add medical_api/models/
git commit -m "Add models via Git LFS"
git push
```

### Option 3: Download Script (For Public Models)

**If models are from HuggingFace/public sources:**

Create `download_models.sh`:
```bash
#!/bin/bash
# Download models from HuggingFace or other sources
mkdir -p medical_api/models/vi_offline
mkdir -p medical_api/models/dia_seg
mkdir -p medical_api/models/dia_embed

# Add download commands here
# wget https://example.com/model.onnx -O medical_api/models/...
```

Then in deployment:
```bash
git pull
./download_models.sh
docker-compose up --build
```

---

## 🔐 Handling Sensitive Files

### Environment Variables (.env)

**Create `.env.example` template (commit this):**

```bash
# .env.example
GROQ_API_KEY=your_key_here
USE_GPU=false
```

**On each machine, create actual `.env` (don't commit):**

```bash
cp .env.example .env
nano .env  # Edit with real values
```

Docker Compose will automatically load `.env` file.

### SSL Certificates

**Never commit certificates to Git!**

```bash
# Keep certs in a secure location
# Copy manually to each server
mkdir -p certs/
cp /secure/storage/fullchain.pem certs/
cp /secure/storage/privkey.pem certs/
chmod 600 certs/*.pem
```

---

## 🧹 Cleaning Up Before Push

### Check What Will Be Committed

```bash
git status
git diff
```

### Remove Accidentally Staged Files

```bash
# If you accidentally added models or certs
git rm --cached -r medical_api/models/
git rm --cached -r certs/

# Commit the removal
git commit -m "Remove large files from git"
```

### Clean Docker Before Push (Optional)

```bash
# Remove unused containers
docker system prune

# Remove old images
docker image prune
```

---

## 📋 Pre-Deployment Checklist

On the **new/existing machine**, before pulling from Git:

### Check Existing Files

```bash
# List what's already there
ls -la medical_api/models/     # Models preserved?
ls -la vibert_pipeline/vibert_cache/  # Cache preserved?
ls -la certs/                  # Certificates present?
```

### Backup Important Files (Optional)

```bash
# If worried about losing something
tar -czf backup_$(date +%Y%m%d).tar.gz \
    medical_api/models/ \
    vibert_pipeline/vibert_cache/ \
    certs/ \
    saved_transcripts/
```

### Pull and Deploy

```bash
git pull
docker-compose down
docker-compose up --build
```

**Result:** 
- ✅ Code updated from Git
- ✅ Models still in place (not in Git)
- ✅ Cache still in place (not in Git)
- ✅ Certs still in place (not in Git)

---

## 🎯 Your Specific Scenario

**Machine already has:**
- ✓ Cache files in `vibert_pipeline/vibert_cache/`
- ✓ Docker images built
- ✓ Models in `medical_api/models/`
- ✓ Certificates in `certs/`

**Steps to deploy from GitHub:**

```bash
# 1. Go to project directory
cd /path/to/medical-asr

# 2. Add remote if not already added
git remote add origin https://github.com/your-username/medical-asr.git

# 3. Pull latest code (preserves non-git files)
git pull origin main

# 4. Check that cache and models are still there
ls vibert_pipeline/vibert_cache/
ls medical_api/models/

# 5. Rebuild (uses Docker cache when possible)
docker-compose build

# 6. Deploy
docker-compose down
docker-compose up -d

# ✅ Done! Cache and models preserved, code updated.
```

---

## 🔍 Verify After Deployment

```bash
# Check containers running
docker ps

# Check API health
curl http://localhost:8000/health

# Check frontend
curl -k https://localhost/

# View logs
docker-compose logs -f
```

---

## 🚨 Troubleshooting

### "Models not found" after git pull

```bash
# Models were accidentally deleted or not copied
# Re-copy from backup or original source
cp -r /backup/models/ medical_api/
```

### "Permission denied" on certs

```bash
# Fix certificate permissions
chmod 600 certs/*.pem
chown $(whoami) certs/*.pem
```

### Docker build not using cache

```bash
# Force rebuild without cache
docker-compose build --no-cache

# Or pull fresh base image
docker pull pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime
docker-compose build
```

### Changes not reflected after pull

```bash
# Hard restart
docker-compose down
docker-compose up --build

# If still not working, remove volumes
docker-compose down -v
docker-compose up --build
```

---

## 📊 Summary

| File Type | In Git? | On Machine? | Action |
|-----------|---------|-------------|--------|
| Python code | ✅ Yes | ✅ Updates | Pull from Git |
| Frontend files | ✅ Yes | ✅ Updates | Pull from Git |
| Config files | ✅ Yes | ✅ Updates | Pull from Git |
| Models | ❌ No | ✅ Preserved | Copy manually once |
| Cache | ❌ No | ✅ Preserved | Auto-generated |
| Certs | ❌ No | ✅ Preserved | Copy manually once |
| .env | ❌ No | ✅ Preserved | Create manually |

---

## 🎓 Best Practices

1. **Never commit sensitive data** (API keys, certificates, passwords)
2. **Use `.gitignore`** properly (already created)
3. **Keep models separate** from code repository
4. **Document deployment** steps for your team
5. **Use `.env.example`** to show required variables
6. **Tag releases** for production deployments:
   ```bash
   git tag -a v2.0 -m "Custom HTML frontend release"
   git push origin v2.0
   ```

---

## ✅ Quick Command Reference

```bash
# First time: Development → GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/user/repo.git
git push -u origin main

# Update: GitHub → Existing Machine (your case)
cd /path/to/project
git pull origin main
docker-compose down
docker-compose up --build

# Update: Development → GitHub
git add .
git commit -m "Description of changes"
git push origin main
```

Your cache files and models are safe! They won't be touched by git operations. 🎉

