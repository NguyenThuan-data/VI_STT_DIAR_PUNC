"""
Custom Exception Classes for Medical ASR System.

Provides specific exception types for different failure modes, enabling
precise error handling and better debugging. All exceptions inherit from
MedicalASRError for catch-all handling when needed.

Exception Hierarchy:
    MedicalASRError (base)
    ├── ModelLoadError (model initialization failures)
    ├── TranscriptionError (ASR processing failures)
    ├── AudioProcessingError (audio file handling failures)
    └── SummarizationError (AI summary generation failures)

Example:
    >>> from medical_api.exceptions import ModelLoadError, MedicalASRError
    >>> 
    >>> try:
    ...     load_asr_model()
    ... except ModelLoadError as e:
    ...     logger.error(f"Model loading failed: {e}")
    ... except MedicalASRError as e:
    ...     logger.error(f"System error: {e}")
"""


class MedicalASRError(Exception):
    """
    Base exception for all Medical ASR system errors.
    
    All custom exceptions inherit from this class, allowing blanket
    exception handling when specific error types don't matter.
    
    Usage:
        Use this as a catch-all when you want to handle any system error:
        
        >>> try:
        ...     process_medical_audio(file)
        ... except MedicalASRError as e:
        ...     # Handles any system-specific error
        ...     return {"error": str(e)}
    """
    pass


class ModelLoadError(MedicalASRError):
    """
    Raised when a machine learning model fails to load or initialize.
    
    Common causes:
        - Model file not found at specified path
        - Corrupted or incomplete model file
        - Insufficient memory (RAM/VRAM) to load model
        - Incompatible model format or version
        - Missing model dependencies
    
    Example:
        >>> import os
        >>> from medical_api.config import ModelConfig
        >>> 
        >>> if not os.path.exists(ModelConfig.ASR_ENCODER):
        ...     raise ModelLoadError(
        ...         f"ASR encoder not found: {ModelConfig.ASR_ENCODER}. "
        ...         f"Please download models first."
        ...     )
    """
    pass


class TranscriptionError(MedicalASRError):
    """
    Raised when audio transcription fails during ASR processing.
    
    Common causes:
        - Invalid or corrupted audio data
        - Empty audio file (no speech detected)
        - Unsupported audio format or codec
        - ASR model inference error
        - Audio sample rate incompatibility
    
    Example:
        >>> import numpy as np
        >>> 
        >>> def transcribe_segment(audio_data):
        ...     if not audio_data.any():
        ...         raise TranscriptionError("Empty audio segment - no data to transcribe")
        ...     # ... transcription logic
    """
    pass


class AudioProcessingError(MedicalASRError):
    """
    Raised when audio file loading or processing fails.
    
    Common causes:
        - File not found or inaccessible
        - Corrupted audio file
        - Unsupported audio codec
        - File format detection failure
        - Audio conversion error
        - File size exceeds limits
    
    Example:
        >>> import librosa
        >>> from medical_api.config import AudioConfig
        >>> 
        >>> try:
        ...     audio, sr = librosa.load(file_path, sr=AudioConfig.SAMPLE_RATE)
        ... except Exception as e:
        ...     raise AudioProcessingError(
        ...         f"Failed to load audio file '{file_path}': {e}"
        ...     ) from e
    """
    pass


class SummarizationError(MedicalASRError):
    """
    Raised when AI summary generation fails.
    
    Common causes:
        - GROQ_API_KEY environment variable not set
        - API authentication failure
        - API rate limit exceeded
        - Network timeout or connection error
        - Invalid API response format
        - Text too long for API
    
    Example:
        >>> import os
        >>> 
        >>> if not os.getenv('GROQ_API_KEY'):
        ...     raise SummarizationError(
        ...         "GROQ_API_KEY environment variable not set. "
        ...         "AI summaries unavailable."
        ...     )
    """
    pass

