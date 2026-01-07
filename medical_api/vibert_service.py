"""
ViBERT Punctuation Service
Integrates ViBERT model for adding punctuation to transcribed text
"""
import os
import sys
import torch

# Global model instance
vibert_model = None

def load_vibert_model():
    """
    Load ViBERT model with hardware awareness
    Returns the loaded model or None if loading fails
    """
    global vibert_model
    
    if vibert_model is not None:
        return vibert_model
    
    try:
        # Add vibert_pipeline to path
        vibert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vibert_pipeline')
        if vibert_path not in sys.path:
            sys.path.insert(0, vibert_path)
        
        from gec_model import GecBERTModel
        
        # Detect hardware
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Resolve vocabulary path
        possible_paths = [
            "./vibert_cache/vocabulary",
            "../vibert_cache/vocabulary",
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


def add_punctuation(text):
    """
    Add punctuation to text using ViBERT model
    
    Args:
        text (str): Raw text without punctuation
        
    Returns:
        str: Text with punctuation added
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


def add_punctuation_batch(texts):
    """
    Add punctuation to multiple texts using ViBERT model (batch processing)
    
    Args:
        texts (list): List of raw texts without punctuation
        
    Returns:
        list: List of texts with punctuation added
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


def is_available():
    """
    Check if ViBERT model is loaded and available
    
    Returns:
        bool: True if model is available, False otherwise
    """
    global vibert_model
    return vibert_model is not None

