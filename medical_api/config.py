"""
Centralized Configuration for Medical ASR System.

This module contains all configuration classes for models, audio processing,
API settings, and system paths. All values support environment variable
overrides for flexible deployment across different environments.

Environment Variables:
    MODEL_DIR: Base directory for model files (default: ./models)
    UPLOAD_DIR: Temporary upload directory (default: uploads)
    USE_GPU: Enable GPU acceleration (default: false)
    GROQ_API_KEY: API key for Groq AI service (required for summaries)

Example:
    >>> from medical_api.config import ModelConfig, AudioConfig
    >>> print(ModelConfig.ASR_ENCODER)
    './models/vi_offline/encoder-epoch-20-avg-10.int8.onnx'
    
    >>> # Override via environment
    >>> import os
    >>> os.environ['MODEL_DIR'] = '/custom/path'
    >>> print(ModelConfig.MODEL_BASE_DIR)
    '/custom/path'
"""

import os
from typing import Final


class ModelConfig:
    """
    Model file paths and loading parameters.
    
    All paths are constructed relative to MODEL_BASE_DIR, which defaults
    to './models' but can be overridden via MODEL_DIR environment variable.
    This allows the same code to work in development, Docker, and production.
    
    Attributes:
        MODEL_BASE_DIR: Base directory containing all model files
        DIA_SEG_MODEL: Path to diarization segmentation ONNX model
        DIA_EMBED_MODEL: Path to speaker embedding extraction ONNX model
        ASR_TOKENS: Path to ASR tokenizer vocabulary file
        ASR_ENCODER: Path to ASR encoder ONNX model (int8 quantized)
        ASR_DECODER: Path to ASR decoder ONNX model (int8 quantized)
        ASR_JOINER: Path to ASR joiner ONNX model (int8 quantized)
        VIBERT_CACHE_DIR: Cache directory for ViBERT model downloads
    
    Example:
        >>> # Docker environment
        >>> ModelConfig.MODEL_BASE_DIR  # '/app/models'
        
        >>> # Local development
        >>> os.environ['MODEL_DIR'] = './my_models'
        >>> ModelConfig.MODEL_BASE_DIR  # './my_models'
    """
    
    # Base directory with environment override support
    MODEL_BASE_DIR: Final[str] = os.getenv("MODEL_DIR", "./models")
    
    # Speaker diarization model paths
    DIA_SEG_MODEL: Final[str] = f"{MODEL_BASE_DIR}/dia_seg/model.onnx"
    DIA_EMBED_MODEL: Final[str] = f"{MODEL_BASE_DIR}/dia_embed/model.onnx"
    
    # ASR (Automatic Speech Recognition) model paths
    # Using int8 quantized models for faster inference with minimal accuracy loss
    ASR_TOKENS: Final[str] = f"{MODEL_BASE_DIR}/vi_offline/tokens.txt"
    ASR_ENCODER: Final[str] = f"{MODEL_BASE_DIR}/vi_offline/encoder-epoch-20-avg-10.int8.onnx"
    ASR_DECODER: Final[str] = f"{MODEL_BASE_DIR}/vi_offline/decoder-epoch-20-avg-10.int8.onnx"
    ASR_JOINER: Final[str] = f"{MODEL_BASE_DIR}/vi_offline/joiner-epoch-20-avg-10.int8.onnx"
    
    # ViBERT model cache (auto-downloaded from HuggingFace)
    VIBERT_CACHE_DIR: Final[str] = "./vibert_cache"


class AudioConfig:
    """
    Audio processing parameters and quality settings.
    
    These constants control how audio files are processed, including
    sample rate conversion, segment filtering, and file size limits.
    
    Attributes:
        SAMPLE_RATE: Target sample rate in Hz (16kHz required by ASR model)
        MIN_SEGMENT_DURATION: Minimum segment length in seconds to keep after diarization.
            Segments shorter than this are filtered as likely noise/artifacts
            - 0.5s: Keeps short interjections but may include noise
            - 1.0s: Good balance for clean recordings (RECOMMENDED)
            - 1.5-2.0s: Use for noisy microphone recordings
        MAX_FILE_SIZE: Maximum allowed upload file size in bytes (500MB)
        NUM_THREADS: Number of CPU threads for ASR processing
        ENABLE_NOISE_REDUCTION: Apply noise reduction preprocessing
        ENABLE_NORMALIZATION: Apply volume normalization
        ENABLE_DEBUG_LOGGING: Print detailed diarization debug information
    
    Notes:
        - 16kHz sample rate balances quality with model requirements
        - Higher MIN_SEGMENT_DURATION reduces over-segmentation (1 person → 3 speakers)
        - Thread count affects CPU usage vs processing speed tradeoff
        - Noise reduction helps with microphone recordings but adds processing time
    """
    
    SAMPLE_RATE: Final[int] = 16000  # 16kHz for ASR compatibility
    MIN_SEGMENT_DURATION: Final[float] = 1.0  # Filter segments < 1.0 seconds (increased from 0.5)
    MAX_FILE_SIZE: Final[int] = 500 * 1024 * 1024  # 500MB upload limit
    NUM_THREADS: Final[int] = 4  # Balance speed vs resource usage
    
    # Audio preprocessing flags
    ENABLE_NOISE_REDUCTION: Final[bool] = True  # Reduce background noise
    ENABLE_NORMALIZATION: Final[bool] = True  # Normalize volume levels
    ENABLE_DEBUG_LOGGING: Final[bool] = False  # Detailed diarization logs


class DiarizationConfig:
    """
    Speaker diarization clustering parameters.
    
    Controls how the system identifies and groups audio segments by speaker.
    The threshold value is critical for balancing over-segmentation (too many
    speakers) vs under-segmentation (merging different speakers).
    
    Attributes:
        CLUSTERING_THRESHOLD: Cosine similarity threshold for speaker clustering.
            Range: 0.0 to 1.0
            - Lower values (0.45-0.50): More speakers, better for similar voices
            - Medium values (0.50-0.55): Balanced, good for most cases
            - Higher values (0.60-0.65): Fewer speakers, use for noisy recordings
            
        NUM_CLUSTERS: Target number of speakers to detect.
            -1 = automatic detection (recommended)
            >0 = force specific number of speakers (use only if known)
            
        MERGE_GAP_THRESHOLD: Maximum gap (seconds) to merge adjacent same-speaker segments
            Helps fix over-segmentation where one person is split into multiple speakers
    
    Scenario-Based Recommendations:
        - High quality studio recording (2 different voices): 0.50
        - Phone/Zoom compressed audio: 0.48
        - Single speaker on microphone: 0.65
        - Noisy environment with multiple speakers: 0.60
        - Same gender/age speakers: 0.45
    
    Example:
        >>> # For 2-person doctor-patient conversation
        >>> DiarizationConfig.CLUSTERING_THRESHOLD = 0.52
        >>> DiarizationConfig.NUM_CLUSTERS = -1  # Auto-detect
    """
    
    CLUSTERING_THRESHOLD: Final[float] = 0.52  # Slightly lower for better separation
    NUM_CLUSTERS: Final[int] = -1  # Auto-detect speaker count
    MERGE_GAP_THRESHOLD: Final[float] = 1.0  # Merge segments if gap < 1.0 second


class APIConfig:
    """
    FastAPI server configuration.
    
    Settings for the API server including network binding, CORS policy,
    and temporary file storage.
    
    Attributes:
        HOST: Server bind address ('0.0.0.0' for all interfaces)
        PORT: Server listen port (8000 is standard for FastAPI)
        UPLOAD_DIR: Temporary directory for uploaded audio files.
            Files are deleted immediately after processing
        CORS_ORIGINS: List of allowed CORS origins for frontend access.
            Use ['*'] for development, specific domains for production
    
    Security Notes:
        - CORS_ORIGINS = ['*'] allows all origins (development only)
        - Production should specify exact frontend domain
        - Uploaded files are automatically cleaned up after processing
    
    Example:
        >>> # Production configuration
        >>> APIConfig.CORS_ORIGINS = ['https://medical-asr.example.com']
    """
    
    HOST: Final[str] = "0.0.0.0"
    PORT: Final[int] = 8000
    UPLOAD_DIR: Final[str] = os.getenv("UPLOAD_DIR", "uploads")
    CORS_ORIGINS: Final[list] = ["*"]  # TODO: Restrict in production

