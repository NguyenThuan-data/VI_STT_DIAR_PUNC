"""
Groq AI Summary Service
Integrates Groq API for generating medical transcription summaries
"""
import os
from groq import Groq

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


def chunk_text(text, max_chars=12000):
    """
    Split text into chunks for processing long documents
    
    Args:
        text (str): Text to split
        max_chars (int): Maximum characters per chunk
        
    Returns:
        list: List of text chunks
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


def call_groq_safe(prompt, system_msg="You are a helpful assistant."):
    """
    Call Groq API with model fallback strategy
    Tries multiple models in order if rate limits are hit
    
    Args:
        prompt (str): User prompt
        system_msg (str): System message
        
    Returns:
        tuple: (response_text, model_used)
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


def generate_summary(full_text):
    """
    Generate summary using Groq API with chunking support
    
    Args:
        full_text (str): Full transcript text
        
    Returns:
        dict: {"summary": str, "model_used": str, "status": str}
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


def is_available():
    """
    Check if Groq service is available
    
    Returns:
        bool: True if Groq client is initialized
    """
    return groq_client is not None

