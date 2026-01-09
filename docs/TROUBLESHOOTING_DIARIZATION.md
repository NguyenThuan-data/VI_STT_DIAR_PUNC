# Troubleshooting Speaker Diarization Issues

Quick guide for diagnosing and fixing speaker identification problems.

---

## 🔍 Problem 1: "2 people detected as 1 speaker" (Under-Segmentation)

### Symptoms
- Multiple people talking, but transcript shows only Speaker_0
- Different voices labeled with same speaker ID
- "Only one person detected" when you know there are multiple

### Root Causes
1. **Threshold too high** - System merging different voices
2. **Very similar voices** - Same gender/age speakers
3. **Poor audio quality** - Compression artifacts making voices similar
4. **Phone/Zoom recording** - Codec destroying voice characteristics

### Solutions (Try in order)

#### Solution 1: Lower Clustering Threshold
```python
# In medical_api/config.py
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.48  # Lower from 0.52 (default)
```

**Test different values:**
- Try 0.48 first (good for most cases)
- Go to 0.45 if still not working (more sensitive)
- Use 0.42 only for very similar voices (same gender/age)

#### Solution 2: Check Recording Quality
- Record with higher sample rate (if possible)
- Use separate microphones for each person
- Avoid heavily compressed formats (MP3 < 128kbps)
- Record in uncompressed WAV if possible

#### Solution 3: Improve Recording Setup
- Position speakers at different angles from microphone
- Ensure adequate distance between speakers
- Use stereo recording (preserves spatial info)
- Avoid phone/Zoom - use local recording instead

#### Solution 4: Enable Debug Mode
```python
# In medical_api/config.py
class AudioConfig:
    ENABLE_DEBUG_LOGGING = True
```

**Check debug output:**
```
Speaker distribution:
  Speaker_0: 45 segments  ← Should see multiple speakers here
  Speaker_1: 0 segments   ← If this is 0, threshold is too high
```

---

## 🔍 Problem 2: "1 person detected as 3 speakers" (Over-Segmentation)

### Symptoms
- Single person talking, transcript shows Speaker_0, Speaker_1, Speaker_2
- Frequent speaker changes during one person's speech
- Non-sequential speaker IDs (Speaker_0, Speaker_5, Speaker_23)

### Root Causes
1. **Background noise** - Noise detected as speech → false speakers
2. **Threshold too low** - System splitting one voice into multiple
3. **Short noise segments** - Not filtered before clustering
4. **Voice changes** - Volume/emotion changes detected as different speaker
5. **Poor microphone** - Handling noise, breath sounds, pops

### Solutions (Try in order)

#### Solution 1: Increase Minimum Segment Duration
```python
# In medical_api/config.py
class AudioConfig:
    MIN_SEGMENT_DURATION = 1.5  # Increase from 1.0 (default)
```

**Test different values:**
- Try 1.5s first (filters more noise)
- Go to 2.0s for very noisy recordings
- Use 1.0s for clean studio recordings

**How it works:** Filters out short segments (< threshold) which are usually noise

#### Solution 2: Raise Clustering Threshold
```python
# In medical_api/config.py
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.60  # Raise from 0.52 (default)
```

**When to use:**
- Single speaker recordings
- Microphone with variable volume
- Speaker with emotional speech (voice changes)

**Test different values:**
- Try 0.60 first
- Go to 0.65 for single-speaker-only recordings

#### Solution 3: Enable Noise Reduction
```python
# In medical_api/config.py (should already be enabled by default)
class AudioConfig:
    ENABLE_NOISE_REDUCTION = True  # Reduces background noise
    ENABLE_NORMALIZATION = True     # Normalizes volume
```

**Impact:**
- Reduces background noise before diarization
- More consistent audio for better clustering
- +10-15% processing time

#### Solution 4: Improve Recording Environment
- Use a quiet room (close windows, turn off AC/fans)
- Use pop filter on microphone
- Maintain consistent distance from mic (20-30cm)
- Use directional microphone (cardioid pattern)
- Avoid touching/moving microphone during recording

#### Solution 5: Check Debug Output
```python
# In medical_api/config.py
class AudioConfig:
    ENABLE_DEBUG_LOGGING = True
```

**Look for:**
```
RAW DIARIZATION OUTPUT
Total segments detected: 87  ← Very high = many noise segments

Speaker distribution:
  Speaker_0: 25 segments
  Speaker_5: 12 segments   ← Gap (no 1-4) = noise filtered
  Speaker_23: 8 segments   ← High number = many noise detections
  Speaker_97: 3 segments   ← Very high = lots of noise
```

**Interpretation:**
- High total segments (> 50 for short audio) = noise problem
- Gaps in speaker IDs = noise segments filtered correctly
- Many speakers (> 5) for single person = threshold too low

---

## 🔍 Problem 3: "Transcript missing words"

### Symptoms
- Some words not transcribed
- Gaps in transcript
- Segments with no text

### Root Causes
1. **Unclear speech** - Mumbling, fast speech, slurred words
2. **Audio quality** - Low volume, distortion, clipping
3. **Unsupported vocabulary** - Very technical/medical jargon
4. **Vietnamese tones** - Incorrect tones make words unrecognizable

### Solutions

#### Solution 1: Improve Speech Quality
- Speak clearly and at normal pace
- Use proper Vietnamese pronunciation and tones
- Avoid shouting (causes distortion)
- Maintain consistent volume

#### Solution 2: Check Audio Quality
```bash
# Check audio properties
ffprobe your_audio.wav

# Should see:
# - Sample rate: 16000 Hz or higher
# - Bit depth: 16 or 24 bit
# - Channels: 1 (mono) or 2 (stereo)
```

#### Solution 3: Enable Normalization
```python
# In medical_api/config.py
class AudioConfig:
    ENABLE_NORMALIZATION = True  # Already default
```

#### Solution 4: Reduce Background Noise
- Record in quieter environment
- Enable noise reduction (default on)
- Use better microphone

---

## 🔍 Problem 4: "Too many noise segments"

### Symptoms
- Debug shows 100+ segments for short audio
- Many speaker IDs (Speaker_50, Speaker_97, etc.)
- Most segments are < 1 second

### Root Causes
1. **Very noisy recording** - AC, fans, typing, etc.
2. **Microphone sensitivity too high** - Picks up everything
3. **Electrical interference** - Buzzing, humming
4. **Poor quality equipment**

### Solutions

#### Solution 1: Aggressive Filtering
```python
# In medical_api/config.py
class AudioConfig:
    MIN_SEGMENT_DURATION = 2.0  # Very aggressive (from 1.0)

class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.65  # Higher threshold
    MERGE_GAP_THRESHOLD = 2.0    # Merge more aggressively (from 1.0)
```

#### Solution 2: Fix Recording Setup
- Turn off air conditioning during recording
- Close windows (street noise)
- Remove fans from room
- Turn off computer monitors (electrical hum)
- Use USB microphone (not 3.5mm jack - less interference)

#### Solution 3: Pre-process Audio
```bash
# Reduce noise using ffmpeg
ffmpeg -i noisy_input.wav -af "afftdn=nf=-25" clean_output.wav
```

---

## 📊 Configuration Matrix

Use this table to quickly find the right settings for your scenario:

| Scenario | Threshold | Min Duration | Merge Gap | Noise Reduction |
|----------|-----------|--------------|-----------|----------------|
| **High quality 2-person** | 0.50 | 0.5s | 1.0s | Off |
| **Office conversation** | 0.52 | 1.0s | 1.0s | On |
| **Phone/Zoom call** | 0.48 | 1.5s | 1.5s | On |
| **Noisy environment** | 0.60 | 2.0s | 2.0s | On |
| **Single speaker mic** | 0.65 | 1.5s | 1.0s | On |
| **Similar voices** | 0.45 | 1.0s | 0.5s | On |
| **Very noisy mic** | 0.70 | 2.5s | 2.0s | On |

---

## 🧪 Step-by-Step Debugging Process

### Step 1: Enable Debug Logging
```python
# medical_api/config.py
class AudioConfig:
    ENABLE_DEBUG_LOGGING = True
```

### Step 2: Run Your Audio File
Upload your audio and check the logs.

### Step 3: Analyze Debug Output

**Look at "Total segments detected":**
- < 20 segments: Normal
- 20-50 segments: Acceptable
- 50-100 segments: Noisy recording
- > 100 segments: Very noisy, need aggressive filtering

**Look at "Speaker distribution":**
```
Speaker_0: 15 segments  ← Main speaker
Speaker_1: 12 segments  ← Second speaker (if 2-person conversation)
Speaker_5: 2 segments   ← Likely noise (filtered)
Speaker_23: 1 segment   ← Definitely noise
```

**Interpretation:**
- 1-2 speakers with balanced distribution = Good
- 3-5 speakers = Possible over-segmentation
- > 5 speakers = Definite over-segmentation or very noisy

### Step 4: Adjust Configuration

**If over-segmentation (too many speakers):**
```python
# Increase both:
AudioConfig.MIN_SEGMENT_DURATION = 1.5  # Higher
DiarizationConfig.CLUSTERING_THRESHOLD = 0.60  # Higher
```

**If under-segmentation (too few speakers):**
```python
# Decrease threshold:
DiarizationConfig.CLUSTERING_THRESHOLD = 0.48  # Lower
```

### Step 5: Test Again
Rebuild and test with same audio:
```bash
cd docker
docker-compose down
docker-compose up --build
```

### Step 6: Iterate
Repeat steps 2-5 until results are satisfactory.

---

## 🎓 Understanding the Numbers

### Clustering Threshold Explained
**Range: 0.0 to 1.0** (cosine similarity)

- **1.0** = Perfectly identical voices (impossible in reality)
- **0.9** = Almost identical (same person, same recording)
- **0.7** = Very similar (same person, different conditions)
- **0.6** = Similar (same gender/age, or single speaker with variations)
- **0.5** = Moderately similar (different people but similar characteristics)
- **0.4** = Different (clear distinction between voices)
- **0.3** = Very different (e.g., male vs female, adult vs child)

**Our range: 0.45 - 0.65**
- Below 0.45: Too sensitive, splits noise as speakers
- Above 0.65: Too conservative, merges different people

### Minimum Segment Duration Explained
**Range: 0.1s to 5.0s**

**Short segments (< 0.5s):**
- Usually breath sounds, pops, typing
- Sometimes very short words ("a", "the", "yes")
- Filter these to reduce noise

**Medium segments (0.5s - 2.0s):**
- Short phrases, interjections
- May be speech or noise
- Balance needed

**Long segments (> 2.0s):**
- Definitely speech
- Never filter these

**Our range: 0.5s - 2.0s**
- 0.5s: Keep short speech, but more noise
- 1.0s: **Balanced (default)**
- 1.5s: Filter more noise, may lose short phrases
- 2.0s: Very clean, but definitely loses short speech

---

## 🔧 Quick Fixes Cheat Sheet

```python
# Copy-paste solutions for medical_api/config.py

# === FIX: 2 people → 1 speaker ===
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.48  # More sensitive

# === FIX: 1 person → 3 speakers ===
class AudioConfig:
    MIN_SEGMENT_DURATION = 1.5  # Filter more noise
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.60  # Less sensitive

# === FIX: Poor quality, lots of noise ===
class AudioConfig:
    MIN_SEGMENT_DURATION = 2.0
    ENABLE_NOISE_REDUCTION = True
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.65
    MERGE_GAP_THRESHOLD = 2.0

# === FIX: Similar voices not separating ===
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.45  # Very sensitive
    MERGE_GAP_THRESHOLD = 0.5    # Merge less

# === FIX: Phone/Zoom recording ===
class AudioConfig:
    MIN_SEGMENT_DURATION = 1.5
    ENABLE_NOISE_REDUCTION = True
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.48

# === FIX: Studio quality, need perfect accuracy ===
class AudioConfig:
    MIN_SEGMENT_DURATION = 0.5  # Keep short speech
    ENABLE_NOISE_REDUCTION = False  # Not needed
class DiarizationConfig:
    CLUSTERING_THRESHOLD = 0.50  # Balanced
```

---

**Remember:** Always rebuild Docker after config changes!
```bash
cd docker
docker-compose down
docker-compose up --build
```

---

**Last Updated**: January 2025 (Version 2.1)

