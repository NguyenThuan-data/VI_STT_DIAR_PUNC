"""
ASR and Speaker Diarization Service.

Handles Sherpa-ONNX model initialization for automatic speech recognition (ASR)
and speaker diarization. Encapsulates all model loading and inference logic,
separating it from the API layer.

This service provides:
    - Speaker diarization (identify who spoke when)
    - Speech-to-text transcription
    - Hardware-aware model loading (CPU/GPU)
    - Model availability checking

Example:
    >>> from medical_api.services.asr_service import ASRService
    >>> 
    >>> # Initialize service with GPU support
    >>> asr = ASRService(use_gpu=True)
    >>> 
    >>> # Check if models loaded successfully
    >>> if asr.is_available():
    ...     # Perform diarization
    ...     segments = asr.diarize_audio(audio_data, sample_rate=16000)
    ...     
    ...     # Transcribe each segment
    ...     for seg in segments:
    ...         text = asr.transcribe_segment(audio_segment, sample_rate=16000)
"""

import os
from typing import Optional, List, Any
import numpy as np
import sherpa_onnx

from medical_api.config import ModelConfig, AudioConfig, DiarizationConfig
from medical_api.exceptions import ModelLoadError, TranscriptionError


class ASRService:
    """
    Automatic Speech Recognition and Speaker Diarization Service.
    
    This class initializes and manages Sherpa-ONNX models for both speaker
    diarization (identifying different speakers) and speech recognition
    (transcribing audio to text). It handles hardware detection (CPU/GPU)
    and provides a clean interface for audio processing.
    
    Attributes:
        diarizer (sherpa_onnx.OfflineSpeakerDiarization): Speaker diarization model
        recognizer (sherpa_onnx.OfflineRecognizer): ASR transcription model
        use_gpu (bool): Whether GPU acceleration is enabled
    
    Example:
        >>> # CPU-only initialization
        >>> asr = ASRService(use_gpu=False)
        >>> 
        >>> # GPU-enabled initialization
        >>> asr = ASRService(use_gpu=True)
        >>> 
        >>> # Check service status
        >>> print(f"ASR ready: {asr.is_available()}")
    """
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize ASR service with speaker diarization and transcription models.
        
        Loads both the diarization model (for identifying speakers) and the
        ASR model (for speech-to-text transcription). Hardware acceleration
        (GPU) is used if available and requested.
        
        Args:
            use_gpu (bool): Enable GPU acceleration if available.
                Defaults to False (CPU-only mode).
        
        Raises:
            ModelLoadError: If models fail to load (missing files, insufficient memory, etc.)
        
        Example:
            >>> # For CPU-only deployment
            >>> asr = ASRService(use_gpu=False)
            
            >>> # For GPU-accelerated deployment
            >>> import os
            >>> use_gpu = os.getenv("USE_GPU", "false").lower() == "true"
            >>> asr = ASRService(use_gpu=use_gpu)
        """
        self.use_gpu = use_gpu
        
        try:
            # Load diarization model (speaker identification)
            print(" Loading Sherpa Diarization...")
            self.diarizer = self._load_diarizer()
            print(" Diarization Ready")
            
            # Load ASR model (speech-to-text)
            print(" Loading Transcription...")
            self.recognizer = self._load_recognizer()
            print(" Transcription Ready")
            
        except Exception as e:
            raise ModelLoadError(f"Failed to initialize ASR service: {e}") from e
    
    def _load_diarizer(self) -> sherpa_onnx.OfflineSpeakerDiarization:
        """
        Load speaker diarization model.
        
        Initializes the Pyannote-based speaker diarization system using
        Sherpa-ONNX. This model identifies different speakers in audio
        and assigns time segments to each speaker.
        
        Returns:
            sherpa_onnx.OfflineSpeakerDiarization: Initialized diarization model
        
        Raises:
            ModelLoadError: If diarization model files are missing or invalid
        
        Note:
            The model requires two components:
            - Segmentation model: Identifies speech regions
            - Embedding model: Creates speaker voice embeddings for clustering
        """
        try:
            # Configure diarization with clustering parameters
            diarization_config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
                # Segmentation: Detect speech regions and boundaries
                segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
                    pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                        model=ModelConfig.DIA_SEG_MODEL,
                    ),
                ),
                # Embedding: Extract voice features for speaker identification
                embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
                    model=ModelConfig.DIA_EMBED_MODEL,
                ),
                # Clustering: Group similar voices together
                clustering=sherpa_onnx.FastClusteringConfig(
                    num_clusters=DiarizationConfig.NUM_CLUSTERS,  # -1 = auto-detect
                    threshold=DiarizationConfig.CLUSTERING_THRESHOLD,  # Similarity threshold
                )
            )
            
            diarizer = sherpa_onnx.OfflineSpeakerDiarization(diarization_config)
            return diarizer
            
        except Exception as e:
            raise ModelLoadError(
                f"Failed to load diarization model. "
                f"Check that model files exist at:\n"
                f"  - {ModelConfig.DIA_SEG_MODEL}\n"
                f"  - {ModelConfig.DIA_EMBED_MODEL}\n"
                f"Error: {e}"
            ) from e
    
    def _load_recognizer(self) -> sherpa_onnx.OfflineRecognizer:
        """
        Load ASR (Automatic Speech Recognition) model.
        
        Initializes the Vietnamese speech-to-text model using Sherpa-ONNX.
        The model is a transducer architecture with encoder, decoder, and
        joiner components (all int8 quantized for efficiency).
        
        Returns:
            sherpa_onnx.OfflineRecognizer: Initialized ASR model
        
        Raises:
            ModelLoadError: If ASR model files are missing or invalid
        
        Note:
            GPU acceleration is used if self.use_gpu is True and CUDA is available.
            Falls back to CPU if GPU is unavailable.
        """
        try:
            # Determine execution provider (CPU or GPU)
            # CUDAExecutionProvider enables GPU acceleration via ONNX Runtime
            provider = "CUDAExecutionProvider" if self.use_gpu else "cpu"
            print(f"   Using provider: {provider}")
            
            # Load Vietnamese transducer ASR model
            # Using int8 quantized models for faster inference with minimal accuracy loss
            recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                tokens=ModelConfig.ASR_TOKENS,
                encoder=ModelConfig.ASR_ENCODER,
                decoder=ModelConfig.ASR_DECODER,
                joiner=ModelConfig.ASR_JOINER,
                num_threads=AudioConfig.NUM_THREADS,
                sample_rate=AudioConfig.SAMPLE_RATE,
                provider=provider,
                decoding_method="greedy_search"  # Fast, deterministic decoding
            )
            
            return recognizer
            
        except Exception as e:
            raise ModelLoadError(
                f"Failed to load ASR model. "
                f"Check that model files exist at:\n"
                f"  - {ModelConfig.ASR_TOKENS}\n"
                f"  - {ModelConfig.ASR_ENCODER}\n"
                f"  - {ModelConfig.ASR_DECODER}\n"
                f"  - {ModelConfig.ASR_JOINER}\n"
                f"Error: {e}"
            ) from e
    
    def diarize_audio(self, audio_data: np.ndarray, sample_rate: int = None) -> List[Any]:
        """
        Perform speaker diarization on audio data.
        
        Identifies different speakers in the audio and segments by speaker.
        Returns a list of segments with start/end times and speaker IDs.
        
        Args:
            audio_data (np.ndarray): Audio waveform as float32 array
            sample_rate (int, optional): Sample rate of audio in Hz.
                Defaults to AudioConfig.SAMPLE_RATE (16000 Hz)
        
        Returns:
            List[Any]: List of diarization segments. Each segment has:
                - start (float): Start time in seconds
                - end (float): End time in seconds
                - speaker (int): Speaker ID (0, 1, 2, ...)
        
        Raises:
            TranscriptionError: If diarization fails
        
        Example:
            >>> import librosa
            >>> audio, sr = librosa.load("audio.wav", sr=16000)
            >>> segments = asr.diarize_audio(audio, sample_rate=16000)
            >>> 
            >>> for seg in segments:
            ...     print(f"Speaker {seg.speaker}: {seg.start:.1f}s - {seg.end:.1f}s")
        """
        if sample_rate is None:
            sample_rate = AudioConfig.SAMPLE_RATE
        
        try:
            # Ensure audio is float32 (required by Sherpa-ONNX)
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Run diarization model
            diar_result = self.diarizer.process(audio_data)
            
            # Sort segments by start time for consistent processing order
            segments = diar_result.sort_by_start_time()
            
            return segments
            
        except Exception as e:
            raise TranscriptionError(f"Speaker diarization failed: {e}") from e
    
    def transcribe_segment(
        self,
        audio_segment: np.ndarray,
        sample_rate: int = None
    ) -> str:
        """
        Transcribe a single audio segment to text.
        
        Converts speech in the audio segment to Vietnamese text using the
        ASR model. This should be called on individual speaker segments
        after diarization.
        
        Args:
            audio_segment (np.ndarray): Audio segment as float32 array
            sample_rate (int, optional): Sample rate in Hz.
                Defaults to AudioConfig.SAMPLE_RATE (16000 Hz)
        
        Returns:
            str: Transcribed text (raw, without punctuation)
        
        Raises:
            TranscriptionError: If transcription fails or audio is invalid
        
        Example:
            >>> # Extract segment audio based on diarization times
            >>> start_idx = int(seg.start * 16000)
            >>> end_idx = int(seg.end * 16000)
            >>> segment_audio = full_audio[start_idx:end_idx]
            >>> 
            >>> # Transcribe the segment
            >>> text = asr.transcribe_segment(segment_audio)
            >>> print(f"Speaker said: {text}")
        """
        if sample_rate is None:
            sample_rate = AudioConfig.SAMPLE_RATE
        
        try:
            # Validate input
            if not isinstance(audio_segment, np.ndarray):
                raise TranscriptionError("Audio segment must be a numpy array")
            
            if len(audio_segment) == 0:
                raise TranscriptionError("Audio segment is empty")
            
            # Ensure audio is float32
            if audio_segment.dtype != np.float32:
                audio_segment = audio_segment.astype(np.float32)
            
            # Create recognition stream
            stream = self.recognizer.create_stream()
            
            # Feed audio to recognizer
            stream.accept_waveform(sample_rate, audio_segment)
            
            # Run recognition
            self.recognizer.decode_stream(stream)
            
            # Extract result text
            result_text = stream.result.text.strip()
            
            return result_text
            
        except TranscriptionError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e
    
    def is_available(self) -> bool:
        """
        Check if ASR service is ready for use.
        
        Verifies that both diarization and transcription models are
        loaded and available for processing.
        
        Returns:
            bool: True if both models are loaded, False otherwise
        
        Example:
            >>> asr = ASRService(use_gpu=False)
            >>> if asr.is_available():
            ...     print("ASR service ready")
            ... else:
            ...     print("ASR service not available")
        """
        return (
            hasattr(self, 'diarizer') and
            self.diarizer is not None and
            hasattr(self, 'recognizer') and
            self.recognizer is not None
        )

