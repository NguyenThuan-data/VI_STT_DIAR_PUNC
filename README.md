# Vietnamese Medical ASR Pipeline — Portfolio Case Study

Professional **demo** medical transcription system: Vietnamese speech-to-text, speaker diarization, punctuation restoration, and AI summarization.

> **Demo only — not for real clinical deployment or production patient data.**  
> **This repo shows architecture and engineering decisions.** Model weights are not included in Git.

---

## Why I built this

During a **software engineering internship in Vietnam**, the team needed to turn long doctor–patient consultations into readable medical notes — not raw ASR dumps. Vietnamese medical speech is noisy, overlapping, and domain-specific. One model is not enough. I built this as a **workplace deliverable**: a full stack from browser UI to multi-model pipeline, with honest limits documented upfront.

## The challenge

- **Technical:** ASR, diarization, punctuation, and summarization had to work as a **pipeline** on CPU — not isolated notebook experiments.
- **Engineering:** Demo users expect a web UI, not a CLI — FastAPI, custom frontend, Docker, Nginx, and health checks.
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

## Demo / proof

| What to review | Where |
|----------------|-------|
| **Architecture & services** | `medical_api/services/` — ASR, diarization, punctuation, Groq modules |
| **API contract** | `medical_api/api.py` — `/api/transcribe`, `/api/summarize`, `/api/health` |
| **Deployment guide** | `docs/DEPLOYMENT.md` — model provisioning, Docker, troubleshooting |
| **Local run (after model setup)** | `uvicorn medical_api.api:app --reload` → [http://localhost:8000/docs](http://localhost:8000/docs) |

**Example workflow:** A ~20-minute consultation recording → diarized, punctuated transcript + optional AI summary (demo exploration only).

> **No hosted demo.** Models (~500MB) and a Groq API key are required. See [Model setup](#-model-setup-required-before-running) below.

### For recruiters (60-second read)

| Question | Answer |
|----------|--------|
| What problem does this solve? | Turn doctor–patient audio into a readable, speaker-labeled transcript + optional summary |
| What was hard? | Orchestrating 4 ML/NLP stages on CPU; tuning diarization in noisy audio; shipping UI → API → Docker |
| Can I run it in one click? | **No** — provision models and `GROQ_API_KEY`. Best path: read case study → skim `medical_api/services/` |

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

---

## Technical reference

### Demo flow

1. **Record or upload audio** — Vietnamese consultation or medical conversation.
2. **Run the pipeline** — ASR → diarization → punctuation → summarization.
3. **Review results** — Speaker-labeled transcript with timestamps and optional AI summary.

### Quick start

> **Prerequisite:** Complete model setup above first.

```bash
git clone https://github.com/NguyenThuan-data/VI_STT_DIAR_PUNC.git
cd VI_STT_DIAR_PUNC
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export GROQ_API_KEY=your_api_key_here
uvicorn medical_api.api:app --reload --host 0.0.0.0 --port 8000
```

Optional frontend: `cd frontend && python -m http.server 3000`

Docker deployment: see **`docs/DEPLOYMENT.md`**.

### Models & capabilities (demo-level)

| Works best | Struggles with |
|------------|----------------|
| Quiet clinic, clear voices | Very noisy environments |
| Phone/Zoom with decent mic | Heavy speaker overlap |
| Single-speaker dictation | Files >1 hour (time/memory) |

### API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Service health |
| POST | `/api/transcribe` | Upload audio → transcript |
| POST | `/api/summarize` | JSON `{ "text": "..." }` → summary |

### Project structure

```text
VI_STT_DIAR_PUNC/
├── frontend/                 # Custom HTML interface
├── medical_api/
│   ├── api.py
│   ├── config.py
│   └── services/             # ASR, audio, ViBERT, Groq
├── docker/
├── nginx/
└── docs/DEPLOYMENT.md
```

### Tech stack

FastAPI · Sherpa-ONNX · Pyannote · ViBERT · Groq · Docker · Nginx · WaveSurfer.js

---

**Version:** 2.2 (Internship context + accessibility level-up link)  
**Last Updated:** 2026-06-11
