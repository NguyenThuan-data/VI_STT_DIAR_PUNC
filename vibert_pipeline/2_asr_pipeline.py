import os
import sys
import time
import subprocess
import requests
import shutil
import uuid
from datetime import datetime
import gradio as gr
from groq import Groq

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠ Warning: PyTorch not found. Defaulting to CPU mode.")

# ===========================
# CONFIGURATION (Environment Variables)
# ===========================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# API Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# .strip() removes accidental spaces from Windows Batch files
ASR_HOST = os.environ.get("ASR_HOST", "127.0.0.1").strip()
ASR_PORT = os.environ.get("ASR_PORT", "8000").strip()
ASR_ENDPOINT = os.environ.get("ASR_ENDPOINT", "/transcribe").strip()
LOCAL_ASR_URL = f"http://{ASR_HOST}:{ASR_PORT}{ASR_ENDPOINT}"

# Pipeline Configuration
INTERFACE_HOST = os.environ.get("INTERFACE_HOST", "127.0.0.1")
INTERFACE_PORT = int(os.environ.get("INTERFACE_PORT", "7860"))

# ===========================
# HARDWARE DETECTION
# ===========================
def detect_hardware():
    """
    Ask the computer what hardware it has.
    Returns: 'cuda' (High Performance) or 'cpu' (Compatibility Mode)
    """
    if not TORCH_AVAILABLE:
        return "cpu"
    
    # Ask PyTorch if an NVIDIA GPU is alive and visible
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"\nHARDWARE: GPU Detected: {gpu_name}")
        print("   -> Mode: HIGH PERFORMANCE (CUDA)")
        return "cuda"
    else:
        print("\nHARDWARE: No GPU detected.")
        print("   -> Mode: COMPATIBILITY (CPU)")
        return "cpu"

# Run detection immediately
DEVICE = detect_hardware()

# ===========================
# LOAD VIBERT MODEL
# ===========================
def load_vibert():
    """Load Vibert model with hardware awareness"""
    try:
        from gec_model import GecBERTModel
        
        # 1. Resolve paths
        possible_paths = [
            "./vibert_cache",
            "../vibert_cache",
            os.path.join(os.getcwd(), "vibert_cache")
        ]
        
        vocab_path = None
        for path in possible_paths:
            test_path = os.path.join(path, "vocabulary")
            if os.path.exists(test_path):
                vocab_path = test_path
                break
        
        if not vocab_path:
            vocab_path = os.path.join(os.getcwd(), "vocabulary")
        
        print(f"   Loading Vibert model on [{DEVICE.upper()}]...")

        # 2. Load Model
        model = GecBERTModel(
            vocab_path=vocab_path,
            model_paths="dragonSwing/vibert-capu",
            split_chunk=True,
            device=DEVICE 
        )
        
        # Manually move to GPU if the wrapper doesn't handle it automatically
        if DEVICE == "cuda" and hasattr(model, 'to'):
             model.to("cuda")

        print("Vibert model loaded successfully")
        return model
    
    except Exception as e:
        print(f"Warning: Could not load Vibert model: {e}")
        return None

vibert_model = load_vibert()


# ===========================
# GROQ API WITH MODEL SWITCHING
# ===========================
def call_groq_safe(client, prompt, system_msg="You are a helpful assistant."):
    """
    Tries multiple models in order. If one fails (Rate Limit), tries the next.
    Returns: (response_text, model_used)
    """
    MODELS = [
        "llama-3.3-70b-versatile",  # 1. Best Intelligence
        "llama-3.1-70b-versatile",  # 2. Backup Intelligence
        "llama-3.1-8b-instant"      # 3. High Speed / High Rate Limits
    ]
    
    for model in MODELS:
        try:
            chat = client.chat.completions.create(
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
            if "rate_limit" in err_msg:
                print(f"⚠ Rate Limit on {model}. Switching to next model...")
                continue
            else:
                return f"Error ({model}): {err_msg}", model
    
    return "All models failed. Please check your API key and try again.", "None"


# ===========================
# AUDIO PROCESSING (ROBUST WINDOWS VERSION)
# ===========================
def safe_copy_audio(input_path):
    """
    Copy audio from restricted Temp folder to a local safe workspace.
    This prevents Windows 'Permission Denied' errors.
    """
    # Create a safe workspace folder if it doesn't exist
    workspace = os.path.join(os.getcwd(), "processing_workspace")
    os.makedirs(workspace, exist_ok=True)

    # Generate unique names to prevent conflicts
    unique_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(input_path)[1]
    safe_path = os.path.join(workspace, f"input_{unique_id}{ext}")
    
    try:
        shutil.copy2(input_path, safe_path)
        return safe_path
    except Exception as e:
        print(f"⚠ Could not copy to safe workspace: {e}")
        return input_path

def compress_audio(input_path):
    """Compress audio using the Safe Workspace strategy"""
    
    # 1. Move to safe zone first
    safe_input = safe_copy_audio(input_path)
    
    # 2. Define output path in the same safe zone
    workspace = os.path.dirname(safe_input)
    unique_id = str(uuid.uuid4())[:8]
    out_path = os.path.join(workspace, f"compressed_{unique_id}.mp3")

    try:
        # Run FFmpeg on the SAFE copy, not the locked Temp file
        subprocess.run([
            "ffmpeg", "-i", safe_input,
            "-ac", "1",      # Mono
            "-b:a", "64k",   # 64kbps
            "-ar", "16000",  # 16kHz
            "-y", out_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print(f"Audio compressed: {os.path.getsize(safe_input)} → {os.path.getsize(out_path)} bytes")
        return out_path
    
    except Exception as e:
        print(f"Compression failed: {e}, using original file")
        return safe_input

def call_asr_api(audio_path):
    """
    Call ASR API with automatic cleanup
    Returns: (response_json, error_message)
    """
    # Use the new robust compression
    upload_path = compress_audio(audio_path)
    
    try:
        print(f"Sending audio to {LOCAL_ASR_URL}...")
        
        with open(upload_path, 'rb') as f:
            resp = requests.post(
                LOCAL_ASR_URL,
                files={'file': (os.path.basename(upload_path), f, 'audio/mpeg')},
                timeout=1800 # 30 mins
            )
        
        if resp.status_code == 200:
            print("ASR API responded successfully")
            return resp.json(), None
        else:
            error_msg = f"API Error {resp.status_code}: {resp.text[:200]}"
            print(f"{error_msg}")
            return None, error_msg

    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to ASR API at {LOCAL_ASR_URL}. Is the API server running?"
    
    except requests.exceptions.Timeout:
        return None, "ASR API timeout. Audio file may be too long."
    
    except Exception as e:
        return None, f"Connection Error: {str(e)}"
        
    finally:
        # CLEANUP: Delete the temp files in workspace
        try:
            if "processing_workspace" in upload_path and os.path.exists(upload_path):
                os.remove(upload_path)
        except:
            pass


# ===========================
# TEXT PROCESSING & SAVING
# ===========================
def run_vibert(text):
    """Add punctuation using Vibert model"""
    if not text or vibert_model is None:
        return text
    
    try:
        res = vibert_model(text.lower().strip())
        return res[0] if isinstance(res, list) and res else str(res)
    except Exception as e:
        print(f"⚠ Vibert error: {e}")
        return text

def chunk_text(text, max_chars=12000):
    """Split text into chunks for processing long documents"""
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    
    for w in words:
        current.append(w)
        current_len += len(w) + 1
        
        if current_len >= max_chars:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
    
    if current:
        chunks.append(" ".join(current))
    
    return chunks

def generate_summary(full_text):
    """Generate summary using Groq API with chunking"""
    if not GROQ_API_KEY:
        return "Missing GROQ_API_KEY environment variable. Set it to enable summaries.", "None"
    
    client = Groq(api_key=GROQ_API_KEY)
    sys_prompt = "You are a medical transcription assistant. Summarize the following medical conversation accurately and concisely."
    
    # Short text
    if len(full_text) < 15000:
        return call_groq_safe(client, full_text, sys_prompt)
    
    # Long text
    print("📄 Long file detected. Using chunking strategy...")
    chunks = chunk_text(full_text)
    partials = []
    
    for i, chunk in enumerate(chunks):
        print(f"   Processing chunk {i+1}/{len(chunks)}...")
        res, model = call_groq_safe(
            client,
            f"Tóm tắt ý chính của đoạn hội thoại y khoa này:\n\n{chunk}",
            sys_prompt
        )
        partials.append(res)
    
    combined = "\n\n".join(partials)
    final_prompt = f"""Tổng hợp các bản tóm tắt sau thành một báo cáo y tế hoàn chỉnh, 
bao gồm: triệu chứng chính, chẩn đoán, và phương pháp điều trị:

{combined}"""
    
    return call_groq_safe(client, final_prompt, sys_prompt)

def save_transcript_to_file(text, summary):
    """
    Save the transcript and summary to a file with Vietnamese naming.
    Format: van_ban_HH_MM_dd_mm_yyyy.txt
    """
    save_folder = "saved_transcripts"
    os.makedirs(save_folder, exist_ok=True)
    
    now = datetime.now()
    filename = now.strftime("van_ban_%H_%M_%d_%m_%Y.txt")
    filepath = os.path.join(save_folder, filename)
    
    content = []
    content.append("="*40)
    content.append(f"NGAY GHI (DATE): {now.strftime('%d/%m/%Y %H:%M:%S')}")
    content.append("="*40)
    content.append("\n--- NOI DUNG CHI TIET (TRANSCRIPT) ---\n")
    content.append(text)
    
    if summary:
        content.append("\n\n" + "="*40)
        content.append("TOM TAT (SUMMARY)")
        content.append("="*40 + "\n")
        content.append(summary)
        
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        return filepath
    except Exception as e:
        print(f"Error saving file: {e}")
        return None


# ===========================
# MASTER PIPELINE
# ===========================
def process_pipeline(audio_path, do_summarize):
    """
    Main processing pipeline
    Returns: (transcript, summary, logs)
    """
    logs = ["="*60, "PIPELINE START", "="*60]
    start_time = time.time()
    
    # Step A: ASR (Speech-to-Text with Diarization)
    logs.append(f"\n[1/3] Calling ASR API at {LOCAL_ASR_URL}...")
    data, err = call_asr_api(audio_path)
    
    if err:
        logs.append(f"✗ ASR Error: {err}")
        logs.append("\nTroubleshooting:")
        logs.append("1. Check if medical_api/api.py is running")
        logs.append("2. Verify ASR_HOST and ASR_PORT in .env")
        logs.append(f"3. Test: curl {LOCAL_ASR_URL}")
        return "", "", "\n".join(logs)
    
    # Step B: Vibert (Add Punctuation)
    logs.append("\n[2/3] Adding punctuation with Vibert...")
    diarized_lines = []
    text_parts = []
    
    for seg in data.get('segments', []):
        speaker = seg.get('speaker', 'Unknown')
        start_time_seg = seg.get('start', 0)
        timestamp = time.strftime('%H:%M:%S', time.gmtime(start_time_seg))
        raw_text = seg.get('text', '')
        
        # Apply punctuation
        punc_text = run_vibert(raw_text) if vibert_model else raw_text
        
        diarized_lines.append(f"[{timestamp}] {speaker}: {punc_text}")
        text_parts.append(punc_text)
    
    full_transcript = "\n".join(diarized_lines)
    full_text_blob = " ".join(text_parts)
    
    logs.append(f"✓ Transcript ready: {len(text_parts)} segments, {len(full_text_blob)} characters")
    
    # Step C: Summary (Optional)
    summary_out = ""
    if do_summarize:
        logs.append("\n[3/3] Generating AI summary...")
        summary_out, model_used = generate_summary(full_text_blob)
        logs.append(f"✓ Summary complete using {model_used}")
    else:
        logs.append("\n[3/3] Summary skipped (disabled by user)")
    
    # Step D: Save to File
    saved_path = save_transcript_to_file(full_transcript, summary_out)
    if saved_path:
        logs.append(f"\nSaved to file: {saved_path}")

    # Final stats
    elapsed = time.time() - start_time
    logs.append(f"\n{'='*60}")
    logs.append(f"PIPELINE COMPLETE in {elapsed:.2f}s")
    logs.append(f"{'='*60}")
    
    return full_transcript, summary_out, "\n".join(logs)


# ===========================
# GRADIO INTERFACE
# ===========================
def interface_fn(audio, do_sum):
    """Gradio interface function"""
    if audio is None:
        return "", "", "Please upload an audio file."
    
    return process_pipeline(audio, do_sum)


def check_api_status():
    """Check if ASR API is accessible"""
    try:
        response = requests.get(f"http://{ASR_HOST}:{ASR_PORT}/docs", timeout=3)
        return f"ASR API is running at {LOCAL_ASR_URL}"
    except:
        return f"ASR API not accessible at {LOCAL_ASR_URL}"


def create_interface():
    """Create Gradio interface"""
    with gr.Blocks(title="CÔNG CỤ CHUYỂN ĐỔI GIỌNG NÓI THÀNH VĂN BẢN(Tối đa 500MB)") as demo:
        
        # Status indicator
        with gr.Row():
            status = gr.Markdown(check_api_status())
        
        gr.Markdown("""
        ### CÁCH SỬ DỤNG
        1. TẢI LÊN TỆP ÂM THANH 
        2. (TÙY CHỌN) TÓM TẮT VỚI AI
        3. BẤM CHẠY VÀ ĐỢI KẾT QUẢ
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                inp = gr.Audio(
                    sources=["upload", "microphone"],
                    type="filepath",
                    label="Input Audio"
                )
                
                chk_sum = gr.Checkbox(
                    label="TÓM TẮT NHANH BẰNG AI",
                    value=False,
                    info="SỬ SỤNG Groq API"
                )
                
                with gr.Row():
                    btn = gr.Button("CHẠY", variant="primary", size="lg")
                    btn_status = gr.Button("Check API Status", size="sm")
            
            with gr.Column(scale=2):
                out_trans = gr.Textbox(
                    label="VĂN BẢN CHUYỂN ĐỔI",
                    lines=12,
                    placeholder="VĂN BẢN CHUYỂN ĐỔI SẼ HIỆN Ở ĐÂY"
                )
                out_sum = gr.Textbox(
                    label="TÓM TẮT",
                    lines=6,
                    placeholder="VĂN BẢN TÓM TẮT SẼ HIỆN Ở ĐÂY"
                )
                out_logs = gr.TextArea(
                    label="System Logs",
                    lines=5,
                    placeholder="Processing logs will appear here..."
                )
        
        # Event handlers
        btn.click(interface_fn, [inp, chk_sum], [out_trans, out_sum, out_logs])
        btn_status.click(lambda: check_api_status(), None, status)
        
        # Footer
        gr.Markdown("""
        ---
        **Configuration**: Edit `.env` file to change ASR API endpoint or other settings.
        """)
    
    return demo


# ===========================
# MAIN
# ===========================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("MEDICAL ASR PIPELINE - LOCAL HOSTING")
    print("="*60)
    print(f"ASR API URL:     {LOCAL_ASR_URL}")
    print(f"Interface URL:   http://{INTERFACE_HOST}:{INTERFACE_PORT}")
    print(f"Groq API Key:    {'Set' if GROQ_API_KEY else 'Missing (summaries disabled)'}")
    print(f"Vibert Model:    {'Loaded' if vibert_model else 'Not loaded'}")
    print("="*60 + "\n")
    
    # Check API status
    print("Checking ASR API connection...")
    print(check_api_status())
    print()
    
    # Create and launch interface
    demo = create_interface()
    
    # Launch configuration
    demo.launch(
        server_name="0.0.0.0",  # "127.0.0.1" for local, "0.0.0.0" for network
        server_port=INTERFACE_PORT,
        share=False,  # Set to True for temporary public link
        debug=True
    )