# Quick Reference - Medical ASR System

## 🚀 Quick Commands

### Start System
```bash
# CPU deployment
cd docker
export GROQ_API_KEY=your_key_here
docker-compose up --build

# GPU deployment (add GPU support)
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up --build

# Background mode (detached)
docker-compose up -d
```

### Stop System
```bash
cd docker
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View Logs
```bash
cd docker
docker-compose logs -f           # All services
docker-compose logs -f asr_app   # Backend only
docker-compose logs -f nginx     # Frontend/proxy only
```

### Rebuild After Code Changes
```bash
cd docker
docker-compose down
docker-compose up --build
```

---

## 🎯 Common Issues & Solutions

### Issue: "2 people → only 1 speaker"
**Solution:** Lower clustering threshold
```python
# In medical_api/config.py
DiarizationConfig.CLUSTERING_THRESHOLD = 0.48  # From 0.52
```

### Issue: "1 person → 3 speakers"
**Solution:** Higher minimum segment duration + higher threshold
```python
# In medical_api/config.py
AudioConfig.MIN_SEGMENT_DURATION = 1.5  # From 1.0
DiarizationConfig.CLUSTERING_THRESHOLD = 0.60  # From 0.52
```

### Issue: "Poor transcription quality"
**Solution:** Check audio quality requirements
1. Enable debug logging: `AudioConfig.ENABLE_DEBUG_LOGGING = True`
2. Review **[AUDIO_QUALITY_GUIDE.md](AUDIO_QUALITY_GUIDE.md)**
3. Improve recording setup (see guide)
4. Enable noise reduction: `AudioConfig.ENABLE_NOISE_REDUCTION = True`

### Issue: "GPU not detected"
**Solution:** Verify CUDA and runtime
```bash
# Check GPU from inside container
docker exec -it medical_asr_system-asr_app-1 nvidia-smi

# If not working, check nvidia-docker runtime
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Issue: "Frontend not loading"
**Solution:** Check service is running
```bash
# Access frontend at http://localhost/ (not http://localhost:8000)
curl http://localhost/

# Check API separately
curl http://localhost:8000/health
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `medical_api/config.py` | **All configuration settings** |
| `AUDIO_QUALITY_GUIDE.md` | **Quality troubleshooting guide** |
| `DEPLOYMENT.md` | Deployment instructions |
| `CHANGELOG.md` | Recent changes |
| `docker/docker-compose.yml` | Docker orchestration |
| `.gitignore` | Files excluded from Git |

---

## 🔧 Configuration Quick Reference

### Audio Quality Settings
```python
# medical_api/config.py

class AudioConfig:
    SAMPLE_RATE = 16000              # Don't change (model requirement)
    MIN_SEGMENT_DURATION = 1.0       # Adjust: 0.5-2.0 seconds
    ENABLE_NOISE_REDUCTION = True    # Toggle: True/False
    ENABLE_NORMALIZATION = True      # Toggle: True/False
    ENABLE_DEBUG_LOGGING = False     # Toggle: True/False for diagnostics
```

### Diarization Settings
```python
# medical_api/config.py

class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.52      # Adjust: 0.45-0.65
    NUM_CLUSTERS = -1                # Don't change (-1 = auto-detect)
    MERGE_GAP_THRESHOLD = 1.0        # Adjust: 0.5-2.0 seconds
```

### Scenario-Based Presets
| Scenario | CLUSTERING_THRESHOLD | MIN_SEGMENT_DURATION |
|----------|---------------------|---------------------|
| **Studio recording** | 0.50 | 0.5s |
| **Office/Medical** (default) | 0.52 | 1.0s |
| **Phone/Zoom** | 0.48 | 1.5s |
| **Noisy environment** | 0.60 | 2.0s |
| **Single speaker mic** | 0.65 | 1.5s |

---

## 🧪 Testing & Debugging

### Enable Debug Mode
```python
# medical_api/config.py
AudioConfig.ENABLE_DEBUG_LOGGING = True
```

### Test Audio File Properties
```bash
# Check audio properties
ffprobe your_audio.wav

# Convert to optimal format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav
```

### API Health Check
```bash
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "medical-asr-api",
  "models_loaded": true,
  "vibert_available": true,
  "groq_available": true
}
```

---

## 📚 Documentation Links

- **Quality Issues?** → [AUDIO_QUALITY_GUIDE.md](AUDIO_QUALITY_GUIDE.md)
- **Deployment Help?** → [DEPLOYMENT.md](DEPLOYMENT.md)
- **Recent Changes?** → [CHANGELOG.md](CHANGELOG.md)
- **API Details?** → http://localhost:8000/docs (after starting)
- **Architecture?** → [medical_api/README.md](medical_api/README.md)

---

## 🆘 Getting Help

1. **Check logs first:**
   ```bash
   cd docker
   docker-compose logs -f
   ```

2. **Enable debug logging:**
   ```python
   # medical_api/config.py
   AudioConfig.ENABLE_DEBUG_LOGGING = True
   ```

3. **Review guides:**
   - Quality issues: **AUDIO_QUALITY_GUIDE.md**
   - Deployment issues: **DEPLOYMENT.md**
   - Configuration: **medical_api/config.py**

4. **Check system health:**
   ```bash
   curl http://localhost:8000/health
   ```

---

**Last Updated:** January 2025 (Version 2.1)
