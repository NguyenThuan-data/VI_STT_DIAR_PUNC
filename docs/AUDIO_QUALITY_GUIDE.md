# Audio Quality Guide for Medical ASR System

## Overview

This guide explains the factors affecting transcription quality and provides recommendations for optimal results with the Vietnamese Medical ASR system.

---

## 📊 Factors Affecting Diarization & Transcription Quality

### 1. **Audio Recording Quality** (Most Critical)

#### Sample Rate
- **Minimum**: 16kHz (system requirement)
- **Recommended**: 16kHz or higher
- **Why**: Higher sample rates preserve more voice characteristics
- **Note**: System automatically resamples to 16kHz

#### Bit Depth
- **Minimum**: 16-bit
- **Recommended**: 24-bit for professional recordings
- **Why**: Higher bit depth = better dynamic range and less quantization noise

#### Signal-to-Noise Ratio (SNR)
- **Minimum**: 20 dB SNR
- **Recommended**: 40+ dB SNR
- **Why**: Background noise confuses the diarization model
- **Impact**:
  - Low SNR (< 20 dB): Poor speaker separation, many false speakers
  - High SNR (> 40 dB): Excellent speaker identification

#### Audio Format
- **Best**: WAV (uncompressed)
- **Good**: FLAC (lossless compression)
- **Acceptable**: MP3 at 320kbps
- **Poor**: MP3 at < 128kbps, heavily compressed formats
- **Why**: Compression artifacts can be mistaken for different speakers

---

### 2. **Recording Environment**

#### Background Noise
| Noise Level | Quality | Diarization Impact |
|-------------|---------|-------------------|
| Quiet room (< 30 dB) | Excellent | Accurate speaker detection |
| Office (30-50 dB) | Good | Minor issues possible |
| Noisy (50-70 dB) | Poor | Many false speakers |
| Very noisy (> 70 dB) | Unusable | System will fail |

**Common Noise Sources:**
- Air conditioning / fans
- Typing on keyboard
- Paper rustling
- Street noise from windows
- Electrical interference

**Solution**: Record in a quiet room or use noise reduction preprocessing

#### Echo & Reverb
- **Problem**: Echo creates "phantom" speakers
- **Cause**: Hard surfaces (walls, windows, tables)
- **Solution**:
  - Use acoustic treatment (curtains, carpets, foam)
  - Record closer to microphone
  - Use directional microphone
  - Enable noise reduction in config

#### Room Acoustics
- **Best**: Treated recording space
- **Good**: Small carpeted room with furniture
- **Poor**: Large empty room with hard surfaces
- **Why**: Reflections degrade voice characteristics

---

### 3. **Microphone & Recording Equipment**

#### Microphone Type
| Type | Best For | Pros | Cons |
|------|---------|------|------|
| **USB Condenser** | Single speaker | Excellent quality | Picks up background noise |
| **Dynamic Mic** | Noisy environment | Rejects background noise | Lower sensitivity |
| **Lavalier** | Multiple speakers | One per person | Requires mixer |
| **Phone/Laptop Mic** | Emergency only | Convenient | Poor quality |

#### Microphone Distance
- **Optimal**: 15-30 cm (6-12 inches) from mouth
- **Too close** (< 10 cm): Plosives (p, b sounds), breathing noise
- **Too far** (> 50 cm): Weak signal, room noise increases
- **Inconsistent distance**: Volume fluctuations → false speakers

#### Recording Setup
**Single Speaker (Microphone):**
- Use directional/cardioid microphone
- Position 20-30cm from mouth
- Use pop filter
- Consistent distance throughout recording

**Multiple Speakers (Conversation):**
- **Best**: Separate microphones for each person
- **Alternative**: Single omnidirectional mic placed equidistant
- **Problem**: Single directional mic → poor separation

---

### 4. **Speaker Characteristics**

#### Voice Similarity
| Scenario | Separation Difficulty | Recommended Threshold |
|----------|----------------------|----------------------|
| Male + Female | Easy | 0.55 |
| Different ages/genders | Easy | 0.52 |
| Same gender, different age | Medium | 0.48 |
| Same gender & age | Hard | 0.45 |
| Very similar voices | Very Hard | 0.42 |

#### Speaking Style
- **Consistent volume**: Better separation
- **Variable volume**: May create false speakers
- **Clear articulation**: Better transcription
- **Mumbling/fast speech**: Poor transcription

#### Emotional Changes
- **Problem**: Voice changes (angry, sad, excited) can be detected as different speakers
- **Solution**: Increase CLUSTERING_THRESHOLD to 0.60-0.65

---

### 5. **Configuration Parameters**

#### CLUSTERING_THRESHOLD
```python
# medical_api/config.py
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.52  # Default
```

**Adjustment Guide:**

| Problem | Symptom | Solution |
|---------|---------|----------|
| Under-segmentation | 2 people → 1 speaker | Lower to 0.45-0.50 |
| Over-segmentation | 1 person → 3 speakers | Raise to 0.60-0.65 |
| Balanced | Correct speaker count | Keep at 0.50-0.55 |

#### MIN_SEGMENT_DURATION
```python
# medical_api/config.py
class AudioConfig:
    MIN_SEGMENT_DURATION = 1.0  # Default (seconds)
```

**Adjustment Guide:**

| Scenario | Recommended Value | Reason |
|----------|------------------|---------|
| Clean studio recording | 0.5s | Keep short interjections |
| Normal office | 1.0s | **Default - balanced** |
| Noisy microphone | 1.5-2.0s | Filter more noise |
| Phone/Zoom call | 1.5s | Compression artifacts |

#### Audio Preprocessing
```python
# medical_api/config.py
class AudioConfig:
    ENABLE_NOISE_REDUCTION = True   # Reduce background noise
    ENABLE_NORMALIZATION = True     # Normalize volume
    ENABLE_DEBUG_LOGGING = False    # Show detailed logs
```

---

## 🎯 Requirements for Good Quality Transcription

### Minimum Requirements
✅ **Audio:**
- Sample rate: 16kHz or higher
- Bit depth: 16-bit minimum
- Format: WAV, FLAC, or MP3 > 128kbps
- Duration: > 5 seconds
- Language: Vietnamese

✅ **Environment:**
- Background noise < 50 dB
- No loud sudden noises
- Minimal echo/reverb

✅ **Speech:**
- Clear articulation
- Normal speaking pace
- Minimal overlapping speech

### Recommended (Professional Quality)
⭐ **Audio:**
- Sample rate: 16kHz (matches model training)
- Bit depth: 24-bit
- Format: WAV uncompressed
- SNR: > 40 dB

⭐ **Recording:**
- Professional microphone (condenser or dynamic)
- 20-30cm microphone distance
- Pop filter/windscreen
- Acoustic treatment

⭐ **Environment:**
- Quiet room (< 30 dB background)
- No air conditioning noise
- Minimal reflections
- Consistent conditions

⭐ **Speakers:**
- One microphone per speaker (ideal)
- Consistent volume throughout
- Minimal overlapping speech
- Clear pronunciation

---

## 🔧 Troubleshooting Common Issues

### Issue 1: "2 people → only Speaker_0"
**Cause**: Under-segmentation (threshold too high for these voices)

**Solutions (try in order):**
1. Lower CLUSTERING_THRESHOLD:
   ```python
   CLUSTERING_THRESHOLD = 0.48  # From 0.52
   ```
2. Check recording quality:
   - Both speakers on same microphone?
   - Similar voice characteristics (same gender/age)?
   - Phone/Zoom compression?
3. Improve audio:
   - Use separate microphones
   - Record in better quality
   - Reduce background noise

### Issue 2: "1 person → 3 speakers"
**Cause**: Over-segmentation (noise, pauses, or threshold too low)

**Solutions (try in order):**
1. Increase MIN_SEGMENT_DURATION:
   ```python
   MIN_SEGMENT_DURATION = 1.5  # From 1.0
   ```
2. Raise CLUSTERING_THRESHOLD:
   ```python
   CLUSTERING_THRESHOLD = 0.60  # From 0.52
   ```
3. Enable noise reduction:
   ```python
   ENABLE_NOISE_REDUCTION = True
   ```
4. Check recording:
   - Microphone handling noise?
   - Background noise (AC, fan)?
   - Echo in the room?

### Issue 3: "Poor transcription accuracy"
**Cause**: Audio quality, speaking style, or background noise

**Solutions:**
1. Improve recording quality (see requirements above)
2. Speak clearly and at normal pace
3. Minimize background noise
4. Ensure consistent microphone distance
5. Use proper Vietnamese pronunciation

### Issue 4: "Words missing or incorrect"
**Cause**: ASR model limitations, unclear speech, or unsupported vocabulary

**Solutions:**
1. Speak more clearly
2. Reduce speech speed
3. Ensure proper Vietnamese tones
4. Check for medical jargon (model trained on general Vietnamese)
5. Review and correct output manually

---

## 📝 Best Practices

### Before Recording
1. ✅ Test audio equipment
2. ✅ Check background noise level
3. ✅ Position microphone correctly
4. ✅ Do a 30-second test recording
5. ✅ Verify test recording quality

### During Recording
1. ✅ Maintain consistent microphone distance
2. ✅ Speak clearly at normal pace
3. ✅ Minimize overlapping speech
4. ✅ Reduce sudden noises (door slams, coughs)
5. ✅ Keep background noise minimal

### After Recording
1. ✅ Check audio file plays correctly
2. ✅ Verify file format and quality
3. ✅ Test with system before important use
4. ✅ Adjust config if needed
5. ✅ Keep backup of original audio

---

## 🧪 Testing Your Audio Quality

### Enable Debug Logging
```python
# medical_api/config.py
class AudioConfig:
    ENABLE_DEBUG_LOGGING = True
```

This will show:
- Raw diarization segments
- Speaker distribution
- Filtered vs original segment counts

### Interpret Debug Output
```
RAW DIARIZATION OUTPUT
Total segments detected: 25

Speaker distribution:
  Speaker_0: 12 segments
  Speaker_1: 8 segments
  Speaker_23: 3 segments  ← Likely noise
  Speaker_97: 2 segments  ← Likely noise
```

**Good**: 2-4 speakers with balanced distribution
**Bad**: 10+ speakers or uneven distribution (one speaker has 1-2 segments)

---

## 📊 Configuration Presets

### Preset 1: Studio Quality Recording
```python
# For professional recordings with good equipment
DiarizationConfig.CLUSTERING_THRESHOLD = 0.50
AudioConfig.MIN_SEGMENT_DURATION = 0.5
AudioConfig.ENABLE_NOISE_REDUCTION = False  # Not needed
```

### Preset 2: Office/Medical Consultation (Default)
```python
# Balanced for typical medical consultations
DiarizationConfig.CLUSTERING_THRESHOLD = 0.52
AudioConfig.MIN_SEGMENT_DURATION = 1.0
AudioConfig.ENABLE_NOISE_REDUCTION = True
```

### Preset 3: Phone/Zoom Calls
```python
# For compressed audio from calls
DiarizationConfig.CLUSTERING_THRESHOLD = 0.48
AudioConfig.MIN_SEGMENT_DURATION = 1.5
AudioConfig.ENABLE_NOISE_REDUCTION = True
```

### Preset 4: Noisy Environment
```python
# For recordings with background noise
DiarizationConfig.CLUSTERING_THRESHOLD = 0.60
AudioConfig.MIN_SEGMENT_DURATION = 2.0
AudioConfig.ENABLE_NOISE_REDUCTION = True
```

### Preset 5: Single Speaker Microphone
```python
# Avoid over-segmentation for solo recordings
DiarizationConfig.CLUSTERING_THRESHOLD = 0.65
AudioConfig.MIN_SEGMENT_DURATION = 1.5
AudioConfig.ENABLE_NOISE_REDUCTION = True
```

---

## 🔬 Advanced: Model Behavior

### How Diarization Works
1. **Segmentation**: Detect speech regions (where someone is speaking)
2. **Embedding**: Extract voice characteristics (pitch, tone, timbre)
3. **Clustering**: Group similar voice embeddings → speaker IDs
4. **Filtering**: Remove short segments (likely noise)
5. **Remapping**: Convert speaker IDs to sequential (0, 1, 2...)

### What Can Go Wrong
- **Segmentation errors**: Background noise detected as speech
- **Embedding errors**: Voice changes (emotion, volume) → different embedding
- **Clustering errors**: Threshold too high/low → wrong grouping
- **Model limitations**: Trained on specific data, may not generalize

### Model Training Data
The Sherpa-ONNX models are trained on:
- General Vietnamese speech
- Various accents and speaking styles
- Clean and moderately noisy audio
- Multiple speakers with varying characteristics

**Not specifically trained on:**
- Medical terminology
- Very noisy environments
- Highly compressed audio
- Vietnamese-English code-switching

---

## 📞 Support & Further Help

### If Quality Issues Persist
1. Enable debug logging and share output
2. Share sample audio (anonymized)
3. Describe recording setup
4. Try different configurations
5. Consider professional recording equipment

### Useful Commands
```bash
# Check audio file properties
ffprobe audio.wav

# Convert to optimal format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav

# Reduce noise (if you have ffmpeg + afftdn)
ffmpeg -i input.wav -af "afftdn=nf=-25" output_clean.wav
```

---

**Last Updated**: January 2025  
**Version**: 2.0 (Clean Architecture Release)

