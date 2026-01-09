# Medical API Architecture

Clean, modular architecture for Vietnamese medical ASR with speaker diarization.

## Folder Structure

```
medical_api/
├── models/                 # Model implementations
│   └── vibert/            # ViBERT punctuation model
│       ├── gec_model.py
│       ├── setup_models.py
│       └── ...
├── services/               # Business logic layer
│   ├── asr_service.py     # ASR + diarization
│   ├── audio_processor.py # Pipeline orchestration
│   ├── vibert_service.py  # Punctuation restoration
│   └── groq_service.py    # AI summarization
├── api.py                  # FastAPI endpoints
├── config.py               # Centralized configuration
└── exceptions.py           # Custom exception types
```

## Architecture Layers

1. **API Layer** (`api.py`): Thin HTTP layer, delegates to services
2. **Service Layer** (`services/`): Business logic and external integrations
3. **Model Layer** (`models/`): ML model implementations
4. **Configuration** (`config.py`): Centralized settings

## Import Patterns

```python
# Import configuration
from medical_api.config import ModelConfig, AudioConfig

# Import services
from medical_api.services.asr_service import ASRService
from medical_api.services import vibert_service, groq_service

# Import exceptions
from medical_api.exceptions import ModelLoadError, TranscriptionError
```

## Example Usage

```python
# Initialize services
asr = ASRService(use_gpu=True)
processor = AudioProcessor(asr, vibert_service)

# Process audio
result = await processor.process_audio_file(uploaded_file)
print(result['text'])  # Formatted transcript
```

## Environment Variables

- `MODEL_DIR`: Base directory for models (default: ./models)
- `UPLOAD_DIR`: Temporary uploads (default: uploads)
- `USE_GPU`: Enable GPU acceleration (default: false)
- `GROQ_API_KEY`: Groq API key for summaries (required for /summarize)

## Documentation Standards

- All classes and functions have Google-style docstrings
- Type hints on all parameters and returns
- Inline comments for complex logic
- Usage examples in docstrings
