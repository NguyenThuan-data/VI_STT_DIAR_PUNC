"""
ViBERT Model Implementation.

Vietnamese BERT-based model for grammar error correction and punctuation
restoration. Used to enhance raw ASR output with proper punctuation.

Main Components:
    - gec_model.py: Main model class (GecBERTModel)
    - modeling_seq2labels.py: Model architecture
    - configuration_seq2labels.py: Model configuration
    - vocabulary.py: Vocabulary handling
    - setup_models.py: Model download and setup utilities

Usage:
    >>> from medical_api.models.vibert.gec_model import GecBERTModel
    >>> model = GecBERTModel(vocab_path="./cache/vocabulary")
    >>> result = model("xin chào bác sĩ")
    >>> print(result)  # "Xin chào bác sĩ."
"""

from .gec_model import GecBERTModel

__all__ = ['GecBERTModel']

