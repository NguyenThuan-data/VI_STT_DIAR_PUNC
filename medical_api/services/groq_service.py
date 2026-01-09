"""
Groq AI Summary Service.

Integrates Groq API for generating medical transcription summaries using
LLaMA language models. Provides automatic text chunking for long documents
and model fallback for rate limiting.

This service handles:
    - Groq API client initialization
    - Text chunking for long transcripts
    - Model fallback strategy (llama-3.3-70b → llama-3.1-70b → llama-3.1-8b)
    - Medical summary generation
    - Error handling and graceful degradation

Example:
    >>> from medical_api.services import groq_service
    >>> 
    >>> # Generate summary
    >>> result = groq_service.generate_summary(transcript_text)
    >>> print(result['summary'])
    >>> print(f"Model used: {result['model_used']}")
"""

import os
from typing import Dict, Any, Tuple
from groq import Groq

from medical_api.exceptions import SummarizationError

# Initialize Groq client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = None

if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✓ Groq API client initialized")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize Groq client: {e}")
else:
    print("⚠ Warning: GROQ_API_KEY not set, summaries will be unavailable")


def chunk_text(text: str, max_chars: int = 12000) -> list:
    """
    Split text into chunks for processing long documents.
    
    Uses word boundaries to avoid splitting mid-word. Essential for
    processing transcripts longer than the model's context window.
    
    Args:
        text (str): Text to split
        max_chars (int): Maximum characters per chunk. Default: 12000
        
    Returns:
        list: List of text chunks
    
    Example:
        >>> long_text = "word " * 10000
        >>> chunks = chunk_text(long_text, max_chars=5000)
        >>> print(f"Split into {len(chunks)} chunks")
    """
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    
    for word in words:
        current.append(word)
        current_len += len(word) + 1
        
        if current_len >= max_chars:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
    
    if current:
        chunks.append(" ".join(current))
    
    return chunks


def call_groq_safe(prompt: str, system_msg: str = "You are a helpful assistant.") -> Tuple[str, str]:
    """
    Call Groq API with model fallback strategy.
    
    Tries multiple models in order if rate limits are hit. This ensures
    the service degrades gracefully under high load.
    
    Args:
        prompt (str): User prompt
        system_msg (str): System message for context
        
    Returns:
        Tuple[str, str]: (response_text, model_used)
    
    Example:
        >>> response, model = call_groq_safe("Summarize: Patient has fever")
        >>> print(f"Response from {model}: {response}")
    """
    if not groq_client:
        return "Groq API not configured. Please set GROQ_API_KEY environment variable.", "None"
    
    MODELS = [
        "llama-3.3-70b-versatile",  # Best intelligence
        "llama-3.1-70b-versatile",  # Backup intelligence
        "llama-3.1-8b-instant"      # High speed / High rate limits
    ]
    
    for model in MODELS:
        try:
            chat = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return chat.choices[0].message.content, model
        
        except Exception as e:
            err_msg = str(e).lower()
            if "rate_limit" in err_msg or "rate limit" in err_msg:
                print(f"⚠ Rate limit on {model}, trying next model...")
                continue
            else:
                return f"Error ({model}): {err_msg}", model
    
    return "All models failed. Please check your API key and try again.", "None"


def generate_summary(full_text: str) -> Dict[str, Any]:
    """
    Generate summary using Groq API with chunking support.
    
    Automatically chunks long transcripts and combines partial summaries.
    Uses medical-specific prompts for accurate medical summarization.
    
    Args:
        full_text (str): Full transcript text
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - status (str): "success" or "error"
            - summary (str): Generated summary
            - model_used (str): LLaMA model version used
    
    Raises:
        SummarizationError: If Groq API is not configured
    
    Example:
        >>> transcript = "[00:00:05] Speaker_0: Xin chào bác sĩ..."
        >>> result = generate_summary(transcript)
        >>> print(result['summary'])
    """
    if not groq_client:
        return {
            "status": "error",
            "summary": "Groq API not configured",
            "model_used": "None"
        }
    
    system_prompt = "You are a medical transcription assistant. Summarize the following medical conversation accurately and concisely."
    
    try:
        # Short text - direct processing
        if len(full_text) < 15000:
            summary, model = call_groq_safe(full_text, system_prompt)
            return {
                "status": "success",
                "summary": summary,
                "model_used": model
            }
        
        # Long text - chunking strategy
        print("📄 Long text detected, using chunking strategy...")
        chunks = chunk_text(full_text)
        partials = []
        
        for i, chunk in enumerate(chunks):
            print(f"   Processing chunk {i+1}/{len(chunks)}...")
            res, model = call_groq_safe(
                f"Tóm tắt ý chính của đoạn hội thoại y khoa này:\n\n{chunk}",
                system_prompt
            )
            partials.append(res)
        
        # Combine partial summaries
        combined = "\n\n".join(partials)
        final_prompt = f"""Summarize the following medical transcription. No explanation needed.

{combined}"""
        
        final_summary, final_model = call_groq_safe(final_prompt, system_prompt)
        
        return {
            "status": "success",
            "summary": final_summary,
            "model_used": final_model
        }
        
    except Exception as e:
        print(f"✗ Summary generation error: {e}")
        return {
            "status": "error",
            "summary": f"Error: {str(e)}",
            "model_used": "None"
        }


def is_available() -> bool:
    """
    Check if Groq service is available.
    
    Verifies that GROQ_API_KEY is set and client is initialized.
    
    Returns:
        bool: True if Groq client is initialized
    
    Example:
        >>> if is_available():
        ...     result = generate_summary(text)
        ... else:
        ...     print("Groq API not configured")
    """
    return groq_client is not None

