"""
FastAPI Application for Medical ASR System.

RESTful API providing Vietnamese medical speech-to-text transcription
with speaker diarization, punctuation restoration, and AI summarization.

Features:
    - Multi-speaker audio transcription
    - Automatic speaker identification and labeling
    - ViBERT-powered punctuation enhancement
    - Groq AI medical summary generation
    - Support for multiple audio formats (MP3, WAV, M4A, OGG, WebM)

API Endpoints:
    GET  /health      - System health and service availability check
    POST /transcribe  - Transcribe audio with speaker diarization
    POST /summarize   - Generate AI summary from transcript

Architecture:
    This module provides a thin HTTP layer. All business logic is
    delegated to the service layer (medical_api/services/) for better
    separation of concerns and testability.

Example Usage:
    Start server:
    >>> uvicorn medical_api.api:app --host 0.0.0.0 --port 8000
    
    Test health:
    >>> curl http://localhost:8000/health
    
    Transcribe audio:
    >>> curl -X POST -F "file=@audio.wav" http://localhost:8000/transcribe

Docker Deployment:
    See docker/docker-compose.yml for production deployment configuration.
"""

import os
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import configuration
from medical_api.config import APIConfig
from medical_api.exceptions import MedicalASRError

# Import services
from medical_api.services.asr_service import ASRService
from medical_api.services.audio_processor import AudioProcessor
from medical_api.services import vibert_service
from medical_api.services import groq_service

# Detect GPU availability from environment
USE_GPU = os.environ.get("USE_GPU", "false").lower() == "true"

# Create uploads directory
os.makedirs(APIConfig.UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI application
app = FastAPI(
    title="Medical ASR API",
    description="Vietnamese medical transcription with speaker diarization and AI summarization",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=APIConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services once at startup (singleton pattern)
# These instances are reused across all requests for efficiency
print("Initializing services...")
asr_service = ASRService(use_gpu=USE_GPU)
audio_processor = AudioProcessor(asr_service, vibert_service)

# Load ViBERT model on startup
print(" Loading ViBERT punctuation model...")
vibert_model = vibert_service.load_vibert_model()
if vibert_model:
    print(" ViBERT Ready")
else:
    print(" ViBERT Not Available (will return unpunctuated text)")

print("✓ All services initialized")


# --- Pydantic Models ---

class SummarizeRequest(BaseModel):
    """
    Request model for summary generation endpoint.
    
    Attributes:
        text: The transcript text to summarize (from /transcribe endpoint)
    """
    text: str


# --- API Endpoints ---

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    System health check endpoint.
    
    Verifies that all critical services are loaded and operational.
    Use this endpoint before processing requests to ensure system readiness.
    
    Returns:
        Dict containing:
            - status (str): "healthy" if system operational
            - service (str): Service identifier
            - models_loaded (bool): ASR models loaded and ready
            - vibert_available (bool): Punctuation service available
            - groq_available (bool): AI summary service available
    
    Example:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/health")
        >>> data = response.json()
        >>> assert data['status'] == 'healthy'
        >>> assert data['models_loaded'] == True
    
    Response (200 OK):
        {
            "status": "healthy",
            "service": "medical-asr-api",
            "models_loaded": true,
            "vibert_available": true,
            "groq_available": true
        }
    """
    return {
        "status": "healthy",
        "service": "medical-asr-api",
        "models_loaded": asr_service.is_available(),
        "vibert_available": vibert_service.is_available(),
        "groq_available": groq_service.is_available()
    }


@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Transcribe audio file with speaker diarization and punctuation.
    
    Processes uploaded audio through the complete pipeline:
    1. Audio loading and format conversion
    2. Speaker diarization (identify who spoke when)
    3. Speech-to-text transcription per speaker
    4. ViBERT punctuation restoration
    5. Formatting with timestamps and speaker labels
    
    Args:
        file: Audio file upload (multipart/form-data)
            Supported formats: MP3, WAV, M4A, OGG, WebM
            Maximum size: 500MB
            Recommended: 16kHz sample rate for best performance
    
    Returns:
        Dict containing:
            - status (str): "success" or "error"
            - text (str): Full formatted transcript with timestamps
            - segments (List[Dict]): Individual segments with metadata
                - start (float): Segment start time in seconds
                - end (float): Segment end time in seconds
                - speaker (str): Speaker identifier (Speaker_0, Speaker_1, etc.)
                - text (str): Transcribed and punctuated text
            - processing_time (float): Total processing time in seconds
    
    Raises:
        HTTPException(500): If transcription fails
    
    Example:
        >>> import requests
        >>> with open('consultation.wav', 'rb') as f:
        ...     files = {'file': f}
        ...     response = requests.post('http://localhost:8000/transcribe', files=files)
        >>> data = response.json()
        >>> print(data['text'])
        [00:00:05] Speaker_0: Xin chào bác sĩ.
        [00:00:08] Speaker_1: Chào bạn, hôm nay cảm thấy thế nào?
    
    Response (200 OK):
        {
            "status": "success",
            "text": "[00:00:05] Speaker_0: Xin chào bác sĩ.\\n[00:00:08] Speaker_1: ...",
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
    """
    try:
        # Delegate all processing to audio_processor service
        # This keeps the API layer thin and testable
        result = await audio_processor.process_audio_file(file)
        return result
        
    except MedicalASRError as e:
        # Log the error for debugging
        print(f"❌ Transcription failed: {e}")
        
        # Return user-friendly error response
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@app.post("/summarize")
async def summarize_endpoint(request: SummarizeRequest) -> Dict[str, Any]:
    """
    Generate AI-powered medical summary from transcript.
    
    Uses Groq API with LLaMA models to generate a concise medical summary.
    Supports long transcripts via automatic chunking. Falls back to faster
    models if rate limits are encountered.
    
    Args:
        request: JSON body containing transcript text
    
    Returns:
        Dict containing:
            - status (str): "success" or "error"
            - summary (str): Generated medical summary
            - model_used (str): LLaMA model version used
    
    Raises:
        HTTPException(400): If text is empty
        HTTPException(500): If summary generation fails
    
    Example:
        >>> import requests
        >>> data = {"text": "[00:00:05] Speaker_0: Xin chào bác sĩ..."}
        >>> response = requests.post('http://localhost:8000/summarize', json=data)
        >>> summary = response.json()['summary']
    
    Response (200 OK):
        {
            "status": "success",
            "summary": "Patient presents with...",
            "model_used": "llama-3.3-70b-versatile"
        }
    
    Notes:
        - Requires GROQ_API_KEY environment variable
        - Long texts (>15000 chars) automatically chunked
        - Model fallback: llama-3.3-70b → llama-3.1-70b → llama-3.1-8b
    """
    try:
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text provided for summarization"
            )
        
        # Generate summary using Groq service
        print("Generating AI summary...")
        result = groq_service.generate_summary(request.text)
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except MedicalASRError as e:
        print(f"❌ Summarization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=APIConfig.HOST,
        port=APIConfig.PORT,
        timeout_keep_alive=None
    )
