"""
Service Layer for Medical ASR System.

Contains all business logic and external service integrations, keeping
the API layer thin and focused on HTTP handling.

Services:
    - ASRService: Speech recognition and speaker diarization
    - AudioProcessor: Audio processing pipeline orchestration
    - ViBERTService: Text punctuation restoration
    - GroqService: AI-powered medical summary generation

Architecture:
    API Layer (api.py)
        └─> Service Layer (services/)
            └─> Model Layer (models/)

Example:
    >>> from medical_api.services import ASRService, AudioProcessor
    >>> asr = ASRService(use_gpu=True)
    >>> processor = AudioProcessor(asr, vibert_service)
"""

from .asr_service import ASRService
from .audio_processor import AudioProcessor
# vibert_service and groq_service are modules, not classes
# Import them in api.py as: from medical_api.services import vibert_service

__all__ = [
    'ASRService',
    'AudioProcessor',
]

