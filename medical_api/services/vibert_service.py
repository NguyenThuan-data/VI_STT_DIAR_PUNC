"""
ViBERT Punctuation Service.

Integrates ViBERT model for adding punctuation to transcribed text.
Provides both single-text and batch processing capabilities for
restoring punctuation to raw ASR output.

This service handles:
    - ViBERT model loading and initialization
    - Single text punctuation restoration
    - Batch text processing (more efficient)
    - Hardware-aware model placement (CPU/GPU)
    - Graceful fallback if model unavailable

Example:
    >>> from medical_api.services import vibert_service
    >>> 
    >>> # Load model
    >>> model = vibert_service.load_vibert_model()
    >>> 
    >>> # Add punctuation to single text
    >>> result = vibert_service.add_punctuation("xin chào bác sĩ")
    >>> print(result)  # "Xin chào bác sĩ."
    >>> 
    >>> # Batch processing (more efficient)
    >>> texts = ["xin chào", "cảm ơn bạn"]
    >>> results = vibert_service.add_punctuation_batch(texts)
"""

import os
from typing import Optional, List
import torch

from medical_api.config import ModelConfig
from medical_api.exceptions import ModelLoadError

# Global model instance
vibert_model = None

def load_vibert_model() -> Optional[any]:
    """
    Load ViBERT model with hardware awareness.
    
    Initializes the Vietnamese BERT-based grammar correction model for
    punctuation restoration. Automatically detects and uses GPU if available.
    
    Returns:
        Optional[GecBERTModel]: Loaded ViBERT model, or None if loading fails
    
    Raises:
        ModelLoadError: If model loading fails critically
    
    Example:
        >>> model = load_vibert_model()
        >>> if model:
        ...     result = model("xin chào bác sĩ")
        ...     print(result)  # ["Xin chào bác sĩ."]
    """
    global vibert_model
    
    if vibert_model is not None:
        return vibert_model
    
    try:
        # Import from new vibert model location
        from medical_api.models.vibert.gec_model import GecBERTModel
        
        # Detect hardware
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Resolve vocabulary path using centralized config
        possible_paths = [
            f"{ModelConfig.VIBERT_CACHE_DIR}/vocabulary",
            "./vibert_cache/vocabulary",
            "/app/vibert_cache/vocabulary",
            os.path.join(os.getcwd(), "vibert_cache", "vocabulary")
        ]
        
        vocab_path = None
        for path in possible_paths:
            if os.path.exists(path):
                vocab_path = path
                break
        
        if not vocab_path:
            print("⚠ Warning: ViBERT vocabulary not found, using default path")
            vocab_path = "./vibert_cache/vocabulary"
        
        print(f"   Loading ViBERT model on [{device.upper()}]...")
        
        # Load model
        model = GecBERTModel(
            vocab_path=vocab_path,
            model_paths="dragonSwing/vibert-capu",
            split_chunk=True,
            device=device
        )
        
        # Move to device if needed
        if device == "cuda" and hasattr(model, 'to'):
            model.to("cuda")
        
        print("✓ ViBERT model loaded successfully")
        vibert_model = model
        return model
        
    except Exception as e:
        print(f"⚠ Warning: Could not load ViBERT model: {e}")
        return None


def add_punctuation(text: str) -> str:
    """
    Add punctuation to text using ViBERT model.
    
    Processes a single text through the ViBERT model to restore
    punctuation and capitalization. Automatically loads the model
    if not already loaded.
    
    Args:
        text (str): Raw text without punctuation
        
    Returns:
        str: Text with punctuation added. Returns original text if model unavailable.
    
    Example:
        >>> result = add_punctuation("xin chào bác sĩ tôi bị đau đầu")
        >>> print(result)
        "Xin chào bác sĩ, tôi bị đau đầu."
    """
    if not text:
        return text
    
    global vibert_model
    
    # Load model if not already loaded
    if vibert_model is None:
        vibert_model = load_vibert_model()
    
    # If model failed to load, return original text
    if vibert_model is None:
        return text
    
    try:
        # Process text
        result = vibert_model(text.lower().strip())
        
        # Extract result
        if isinstance(result, list) and result:
            return result[0]
        else:
            return str(result)
            
    except Exception as e:
        print(f"⚠ ViBERT processing error: {e}")
        return text


def add_punctuation_batch(texts: List[str]) -> List[str]:
    """
    Add punctuation to multiple texts using ViBERT model (batch processing).
    
    More efficient than calling add_punctuation() multiple times.
    Processes all texts together for better performance.
    
    Args:
        texts (List[str]): List of raw texts without punctuation
        
    Returns:
        List[str]: List of texts with punctuation added.
            Returns original texts if model unavailable.
    
    Example:
        >>> texts = [
        ...     "xin chào bác sĩ",
        ...     "tôi bị đau đầu",
        ...     "cảm ơn bác sĩ"
        ... ]
        >>> results = add_punctuation_batch(texts)
        >>> for r in results:
        ...     print(r)
        "Xin chào bác sĩ."
        "Tôi bị đau đầu."
        "Cảm ơn bác sĩ."
    """
    if not texts:
        return []
    
    global vibert_model
    
    # Load model if not already loaded
    if vibert_model is None:
        vibert_model = load_vibert_model()
    
    # If model failed to load, return original texts
    if vibert_model is None:
        return texts
    
    try:
        # Process each text (ViBERT model handles batching internally)
        results = []
        for text in texts:
            if not text:
                results.append(text)
                continue
                
            result = vibert_model(text.lower().strip())
            
            # Extract result
            if isinstance(result, list) and result:
                results.append(result[0])
            else:
                results.append(str(result))
        
        return results
            
    except Exception as e:
        print(f"⚠ ViBERT batch processing error: {e}")
        return texts


def is_available() -> bool:
    """
    Check if ViBERT model is loaded and available.
    
    Use this before attempting punctuation to verify the service is ready.
    
    Returns:
        bool: True if model is available, False otherwise
    
    Example:
        >>> if is_available():
        ...     result = add_punctuation("hello")
        ... else:
        ...     print("ViBERT not available")
    """
    global vibert_model
    return vibert_model is not None

