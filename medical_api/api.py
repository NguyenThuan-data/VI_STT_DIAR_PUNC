from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import shutil
import os
import soundfile as sf
import librosa
import numpy as np
import sherpa_onnx
import time

# Import our custom services
import medical_api.vibert_service as vibert_service
import medical_api.groq_service as groq_service
# ==========================================
# 1. SETUP
# ==========================================
# check if the computer having cuda/cpu
USE_GPU = os.environ.get("USE_GPU", "false").lower() == "true"


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Medical ASR API (Final)")

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. LOAD MODELS
# ==========================================
print(" Loading Sherpa Diarization...")
diarization_config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
    segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
        pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
            model="./models/dia_seg/model.onnx",
        ),
    ),
    embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
        model="./models/dia_embed/model.onnx",
    ),
    clustering=sherpa_onnx.FastClusteringConfig(
        num_clusters=-1, 
        threshold=0.6  # Increased from 0.5 to reduce over-segmentation
    )

)
diarizer = sherpa_onnx.OfflineSpeakerDiarization(diarization_config)
print(" Diarization Ready")

print(" Loading Transcription...")
recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
    tokens="./models/vi_offline/tokens.txt",
    encoder="./models/vi_offline/encoder-epoch-20-avg-10.int8.onnx",
    decoder="./models/vi_offline/decoder-epoch-20-avg-10.int8.onnx",
    joiner="./models/vi_offline/joiner-epoch-20-avg-10.int8.onnx",
    num_threads=4, 
    sample_rate=16000, 
    provider="cuda" if USE_GPU else "cpu",
    decoding_method="greedy_search"
)
print(" Transcription Ready")

# Load ViBERT model on startup
print(" Loading ViBERT punctuation model...")
vibert_model = vibert_service.load_vibert_model()
if vibert_model:
    print(" ViBERT Ready")
else:
    print(" ViBERT Not Available (will return unpunctuated text)")

# ==========================================
# 3. REQUEST/RESPONSE MODELS
# ==========================================
class SummarizeRequest(BaseModel):
    text: str

# ==========================================
# 4. ENDPOINTS
# ==========================================
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "medical-asr-api",
        "models_loaded": True,
        "vibert_available": vibert_service.is_available(),
        "groq_available": groq_service.is_available()
    }
@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """
    Main transcription endpoint with diarization and punctuation
    """
    file_path = f"{UPLOAD_DIR}/{file.filename}"
    clean_wav_path = f"{UPLOAD_DIR}/clean_{os.path.splitext(file.filename)[0]}.wav"
    
    start_time = time.time()
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Load & Convert
        print("   -> Loading audio file...")
        y, sr = librosa.load(file_path, sr=16000)
        sf.write(clean_wav_path, y, 16000)
        
        print("   -> Running Diarization...")
        diar_result = diarizer.process(y)
        all_segments = diar_result.sort_by_start_time()
        
        # Filter out very short segments (likely noise or false detections)
        min_duration = 0.5  # seconds
        segments = [seg for seg in all_segments if (seg.end - seg.start) >= min_duration]
        
        print(f"   -> Filtered segments: {len(all_segments)} → {len(segments)} (removed segments < {min_duration}s)")
        
        full_transcript = ""
        output_segments = []
        
        # Process Segments
        print(f"   -> Found {len(segments)} segments. Transcribing...")
        audio_data = y.astype(np.float32)
        
        # Step 1: Transcribe all segments and collect raw texts
        raw_segments = []
        for seg in segments:
            start_sec = seg.start
            end_sec = seg.end
            speaker_label = f"Speaker_{seg.speaker}" 
            
            # Slice Audio
            start_idx = int(start_sec * 16000)
            end_idx = int(end_sec * 16000)
            
            if end_idx > len(audio_data): 
                end_idx = len(audio_data)
            segment_audio = audio_data[start_idx:end_idx]
            
            # Transcribe
            s = recognizer.create_stream()
            s.accept_waveform(16000, segment_audio)
            recognizer.decode_stream(s)
            raw_text = s.result.text.strip()
            
            if raw_text:
                raw_segments.append({
                    "start": start_sec,
                    "end": end_sec,
                    "speaker": speaker_label,
                    "raw_text": raw_text
                })
        
        # Step 2: Batch punctuation processing (faster!)
        print(f"   -> Adding punctuation to {len(raw_segments)} segments (batch mode)...")
        if raw_segments:
            raw_texts = [seg["raw_text"] for seg in raw_segments]
            punctuated_texts = vibert_service.add_punctuation_batch(raw_texts)
            
            # Step 3: Format output
            for seg_data, punctuated_text in zip(raw_segments, punctuated_texts):
                timestamp = time.strftime('%H:%M:%S', time.gmtime(seg_data["start"]))
                line = f"[{timestamp}] {seg_data['speaker']}: {punctuated_text}"
                full_transcript += line + "\n"
                
                output_segments.append({
                    "start": seg_data["start"],
                    "end": seg_data["end"],
                    "speaker": seg_data["speaker"],
                    "text": punctuated_text
                })
        
        elapsed = time.time() - start_time
        print(f"   -> Transcription complete in {elapsed:.2f}s")
        
        return {
            "status": "success",
            "text": full_transcript,
            "segments": output_segments,
            "processing_time": elapsed
        }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
        
    finally:
        if os.path.exists(file_path): 
            os.remove(file_path)
        if os.path.exists(clean_wav_path): 
            os.remove(clean_wav_path)


@app.post("/summarize")
async def summarize_endpoint(request: SummarizeRequest):
    """
    Generate AI summary of transcribed text using Groq API
    """
    try:
        if not request.text:
            return {
                "status": "error",
                "message": "No text provided"
            }
        
        print("   -> Generating summary...")
        result = groq_service.generate_summary(request.text)
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "status": "error",
            "message": str(e),
            "summary": "",
            "model_used": "None"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=None)


