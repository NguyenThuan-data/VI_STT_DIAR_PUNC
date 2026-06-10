# Vietnamese Medical ASR Pipeline — Portfolio Case Study

Professional **demo** medical transcription system: Vietnamese speech-to-text, speaker diarization, punctuation restoration, and AI summarization.

> **Demo only — not for real clinical deployment or production patient data.**  
> **This repo shows architecture and engineering decisions.** Model weights are not included in Git.

---

## For recruiters (60-second read)

| Question | Answer |
|----------|--------|
| What problem does this solve? | Turn a doctor–patient audio recording into a readable, speaker-labeled transcript + optional summary |
| What was hard? | Orchestrating 4 ML/NLP stages with acceptable latency on CPU; tuning diarization in noisy audio; shipping a full stack (UI → API → Docker) |
| What does this repo prove? | I can design and implement an **end-to-end applied AI system**, not just a notebook |
| Can I run it in one click? | **No** — you need to provision models (~500MB) and a Groq API key. See [Model setup](#-model-setup-required-before-running) below |
| Best way to evaluate | Read this case study → skim `medical_api/services/` → review screenshots in `docs/` (if present) → optional local run after model setup |

---

## The challenge

- **Technical:** Vietnamese medical speech is noisy, overlapping, and domain-specific. One model is not enough — I needed ASR, diarization, punctuation, and summarization to work as a **pipeline**, not isolated scripts.
- **Engineering:** Recruiters and demo users expect a web UI, not a CLI. That meant FastAPI, a custom frontend, Docker, Nginx, and honest health/observability — while staying on CPU for accessibility.
- **Expectations:** Calling this "medical" raises the bar. I chose to be explicit: this is a **portfolio demo**, not a regulated device.

## What I did

1. Designed a **thin API layer** (`medical_api/api.py`) over service modules (ASR, audio, ViBERT, Groq).
2. Built a **custom frontend** (HTML/CSS/JS + WaveSurfer) — no Streamlit — for waveform UX and recording.
3. Wired **offline ASR** (Sherpa-ONNX) + **Pyannote diarization** + **ViBERT punctuation** + **Groq summarization**.
4. Containerized with Docker Compose, Nginx reverse proxy, and CPU/GPU profiles.
5. Documented limitations (noise, overlap, long files) instead of overselling accuracy.

## What I learned

- Production ML is mostly **integration, config, and failure modes** — not benchmark scores in a notebook.
- Diarization thresholds (`CLUSTERING_THRESHOLD`, segment duration) matter as much as model choice.
- Large artifacts (models, certs) belong **outside Git** with clear setup docs — otherwise clones fail and reviewers bounce.
- Honest "works best / struggles with" tables build more trust than claiming hospital-ready.

## How this leveled me up

| | |
|---|---|
| **Before** | I could train or call individual models in isolation |
| **After** | I can ship a multi-model pipeline with UI, API contracts, Docker deployment, and operational docs |
| **Unlocked next** | Accessibility QA on real UIs, agent/MCP tooling, and larger speech+LLM products |

---

## ⚠️ Model setup required before running

**Cloning alone is not enough.** The following are **gitignored** and must be provisioned locally:

| Asset | Location | Size (approx.) |
|-------|----------|----------------|
| Vietnamese ASR (Sherpa-ONNX) | `medical_api/models/vi_offline/` | ~300MB+ |
| Diarization models | `medical_api/models/dia_seg/`, `dia_embed/` | ~100MB+ |
| ViBERT cache | auto-download on first run | varies |
| SSL certs (Docker deploy) | `certs/` | use `generate_cert.py` for dev |
| Groq API key | env `GROQ_API_KEY` | required for summarization |

Full checklist: **`docs/DEPLOYMENT.md`** → *Prerequisites → Required Files*.

Without models, `/api/transcribe` will fail — that is expected. Review the code and docs first; run locally only if you need hands-on verification.

---

## 💡 About the project

- **Faster documentation**: Turns a Vietnamese doctor–patient conversation audio file into a structured transcript plus short summary.
- **Clear speaker separation**: Automatically labels who is speaking (e.g. doctor vs patient) with timestamps.
- **Higher readability**: Restores punctuation and capitalization so transcripts look like real medical notes, not raw ASR output.
- **End-to-end system**: Custom web UI → FastAPI backend → ASR + diarization + ViBERT + LLM summarization → Docker/Nginx deployment.

**Example demo workflow:** A 20-minute consultation recording is uploaded → the system produces a diarized, punctuated transcript and an AI-generated summary (demo exploration only).

---

## 🎯 Key Features

- **Vietnamese ASR** – Offline speech recognition using Sherpa-ONNX.
- **Speaker Diarization** – Automatic speaker identification and labeling.
- **Punctuation Restoration** – ViBERT-powered punctuation enhancement for Vietnamese.
- **AI Summarization** – Groq API integration with LLaMA-family models.
- **Professional Web Interface** – Custom HTML/CSS/JavaScript frontend (no low-code framework).
- **Audio Waveform Visualization** – WaveSurfer.js with click-to-seek and auto-pause.
- **Microphone Recording** – Browser-based audio capture.
- **Audio Quality Enhancement** – Noise reduction and volume normalization.
- **SSL/HTTPS via Nginx** – Reverse proxy and HTTPS in the Docker deployment.
- **CPU/GPU Support** – Flexible docker-compose configs for CPU servers and GPU servers.

---

## 🧭 What This Project Demonstrates

- **End-to-end ML system design** — Browser frontend, FastAPI backend, audio processing pipeline, and multi-model orchestration.
- **Applied speech + NLP** — Sherpa-ONNX, Pyannote, ViBERT, and an LLM for summarization.
- **Production-style engineering** — Docker, docker-compose, Nginx, HTTPS, health checks, and resource constraints.
- **Configuration and observability** — Centralized `config.py`, health endpoints, logs, and explicit thresholds.
- **Pragmatic trade-offs** — Documented limits instead of pretending hospital production-readiness.

---

## 🧪 Demo Flow

1. **Record or upload audio** – A Vietnamese consultation or medical conversation.
2. **Run the pipeline** – ASR → diarization → punctuation → summarization.
3. **Review results** – Speaker-labeled transcript with timestamps and optional AI summary.
4. **Copy output** – Demo exploration only; not for real EMR use.

---

## 🚀 Quick Start

> **Prerequisite:** Complete [model setup](#-model-setup-required-before-running) first.

### Option A – Local Dev (CPU, No SSL)

1. **Clone and install** (Python 3.10+):

```bash
git clone https://github.com/NguyenThuan-data/VI_STT_DIAR_PUNC.git
cd VI_STT_DIAR_PUNC
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Provision models** into `medical_api/models/` (see `docs/DEPLOYMENT.md`).

3. **Set Groq API key:**

```bash
export GROQ_API_KEY=your_api_key_here  # PowerShell: $env:GROQ_API_KEY="your_api_key_here"
```

4. **Start FastAPI:**

```bash
uvicorn medical_api.api:app --reload --host 0.0.0.0 --port 8000
```

5. **Verify:** `http://localhost:8000/docs` → `/api/health`, then `/api/transcribe` with a short audio file.

6. **(Optional) Frontend:**

```bash
cd frontend && python -m http.server 3000
```

Open `http://localhost:3000` (configure API URL to `http://localhost:8000` if needed).

### Option B – Docker Deployment

See **`docs/DEPLOYMENT.md`** for CPU/GPU compose commands, certificates, and troubleshooting.

**Access (when deployed):**

- **Main Interface:** `https://localhost/`
- **API Docs:** `http://localhost:8000/docs`
- **Health:** `http://localhost:8000/health`

---

## 📁 Project Structure (Simplified)

```text
project/
├── docker/                   # Docker configuration
├── frontend/                 # Custom HTML interface
├── medical_api/              # Backend API
│   ├── api.py                # FastAPI endpoints
│   ├── config.py             # Centralized configuration
│   └── services/             # ASR, audio, ViBERT, Groq
├── nginx/                    # Reverse proxy
├── certs/                    # SSL (not in Git)
└── docs/                     # DEPLOYMENT.md, guides
```

---

## 🔍 Models & Capabilities (Demo-Level)

### Works Best For

| Scenario | Expected Quality |
|----------|------------------|
| Quiet clinic room, clear voices | High transcription accuracy, stable diarization |
| Phone/Zoom with decent microphone | Good transcription; diarization depends on noise |
| Single speaker (dictation-style) | Very strong transcription, simple segmentation |

### Struggles With

| Scenario | Limitations |
|----------|-------------|
| Very noisy environments | Diarization less reliable |
| Heavy overlap (interruptions) | ASR and diarization less stable |
| Extremely long files (>1 hour) | Processing time and memory increase |

See `medical_api/config.py` and **AUDIO_QUALITY_GUIDE.md** for tuning.

---

## 🔧 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Service health |
| POST | `/api/transcribe` | Upload audio → transcript |
| POST | `/api/summarize` | JSON body `{ "text": "..." }` → summary |

Interactive docs at `/docs` when the backend is running.

---

## 📖 Additional Documentation

- **docs/DEPLOYMENT.md** — Model provisioning, Docker, updates, troubleshooting
- **AUDIO_QUALITY_GUIDE.md** — Audio quality factors and threshold presets
- **medical_api/README.md** — Backend architecture

---

## 🛠️ Technology Stack

**Frontend:** HTML5, CSS3, Vanilla JS, WaveSurfer.js  
**Backend:** FastAPI, Sherpa-ONNX, Pyannote, ViBERT, Groq API, Librosa, pydub  
**Infrastructure:** Docker, Nginx, PyTorch (optional GPU)

---

## 🙏 Acknowledgments

Sherpa-ONNX · Pyannote · ViBERT · Groq · WaveSurfer.js

---

**Version:** 2.1 (Portfolio case-study README)  
**Last Updated:** 2026-06-11
