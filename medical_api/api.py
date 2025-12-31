from fastapi import FastAPI, UploadFile, File
import uvicorn
import shutil
import os
import soundfile as sf
import librosa
import numpy as np
import sherpa_onnx

# ==========================================
# 1. SETUP
# ==========================================
# check if the computer having cuda/cpu
USE_GPU = os.environ.get("USE_GPU", "false").lower() == "true"


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Medical ASR API (Final)")

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
        threshold=0.5
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

# ==========================================
# 3. ENDPOINT
# ==========================================
@app.get("/health")
async def health_check():
    return {
	"status":"healthy",
	"service":"medical-asr-api",	
	"models_loadeds":True
}
@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    file_path = f"{UPLOAD_DIR}/{file.filename}"
    clean_wav_path = f"{UPLOAD_DIR}/clean_{os.path.splitext(file.filename)[0]}.wav"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Load & Convert
        y, sr = librosa.load(file_path, sr=16000)
        sf.write(clean_wav_path, y, 16000)
        
        print("   -> Running Diarization...")
        diar_result = diarizer.process(y)
        
        # --- FIX: CALL THE SORT METHOD TO GET THE LIST ---
        # The debug info showed 'sort_by_start_time' exists.
        # Calling this returns the actual list of segments we can loop over.
        segments = diar_result.sort_by_start_time()
        
        full_transcript = ""
        output_segments = []
        
        # Process Segments
        print(f"   -> Found {len(segments)} segments. Transcribing...")
        audio_data = y.astype(np.float32)
        
        for seg in segments:
            # seg is now a valid object with .start, .end, .speaker
            start_sec = seg.start
            end_sec = seg.end
            speaker_label = f"Speaker_{seg.speaker}" 
            
            # Slice Audio
            start_idx = int(start_sec * 16000)
            end_idx = int(end_sec * 16000)
            
            if end_idx > len(audio_data): end_idx = len(audio_data)
            segment_audio = audio_data[start_idx:end_idx]
            
            # Transcribe
            s = recognizer.create_stream()
            s.accept_waveform(16000, segment_audio)
            recognizer.decode_stream(s)
            text = s.result.text.strip()
            
            if text:
                line = f"[{start_sec:.1f}s - {end_sec:.1f}s] {speaker_label}: {text}"
                full_transcript += line + "\n"
                
                output_segments.append({
                    "start": start_sec,
                    "end": end_sec,
                    "speaker": speaker_label,
                    "text": text
                })
        
        return {
            "status": "success",
            "text": full_transcript,
            "segments": output_segments
        }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
        
    finally:
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(clean_wav_path): os.remove(clean_wav_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=None)


