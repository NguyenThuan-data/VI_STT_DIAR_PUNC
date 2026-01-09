"""
Audio Processing Pipeline Service.

Orchestrates the complete audio processing workflow from file upload through
transcription, punctuation, and formatting. Coordinates between ASR, diarization,
and punctuation services to produce final transcripts.

This service handles:
    - Audio file loading and conversion
    - Segment filtering (removing noise)
    - Speaker ID remapping (sequential numbering)
    - Pipeline coordination
    - Result formatting

Example:
    >>> from medical_api.services import ASRService, AudioProcessor
    >>> from medical_api.services import vibert_service
    >>> 
    >>> asr = ASRService(use_gpu=False)
    >>> processor = AudioProcessor(asr, vibert_service)
    >>> 
    >>> result = await processor.process_audio_file(uploaded_file)
    >>> print(result['text'])  # Formatted transcript
"""

import os
import time
import shutil
from typing import Dict, List, Any
import numpy as np
import librosa
import soundfile as sf
from fastapi import UploadFile

from medical_api.config import AudioConfig
from medical_api.exceptions import AudioProcessingError, TranscriptionError


class AudioProcessor:
    """
    Audio processing pipeline orchestrator.
    
    Coordinates the complete workflow: audio loading → diarization →
    segment filtering → transcription → punctuation → formatting.
    
    Attributes:
        asr_service: ASR and diarization service instance
        vibert_service: Punctuation restoration service module
    
    Example:
        >>> processor = AudioProcessor(asr_service, vibert_service)
        >>> result = await processor.process_audio_file(file)
        >>> print(f"Processed {len(result['segments'])} segments")
    """
    
    def __init__(self, asr_service, vibert_service):
        """
        Initialize audio processor with required services.
        
        Args:
            asr_service: ASRService instance for transcription and diarization
            vibert_service: ViBERT service module for punctuation
        """
        self.asr_service = asr_service
        self.vibert_service = vibert_service
    
    async def process_audio_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process uploaded audio file through complete pipeline.
        
        Complete workflow:
        1. Save uploaded file temporarily
        2. Load and convert audio to target format
        3. Perform speaker diarization
        4. Filter out short segments (noise)
        5. Remap speaker IDs to sequential numbers
        6. Transcribe each segment
        7. Add punctuation (batch processing)
        8. Format output with timestamps
        9. Clean up temporary files
        
        Args:
            file: Uploaded audio file (FastAPI UploadFile)
        
        Returns:
            Dict containing:
                - status: "success" or "error"
                - text: Full formatted transcript
                - segments: List of individual segments with metadata
                - processing_time: Total time in seconds
        
        Raises:
            AudioProcessingError: If audio file processing fails
            TranscriptionError: If transcription fails
        
        Example:
            >>> files = {'file': open('audio.wav', 'rb')}
            >>> response = requests.post('/transcribe', files=files)
            >>> result = response.json()
        """
        file_path = f"{AudioConfig.UPLOAD_DIR}/{file.filename}"
        clean_wav_path = f"{AudioConfig.UPLOAD_DIR}/clean_{os.path.splitext(file.filename)[0]}.wav"
        
        start_time = time.time()
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            # Step 1: Load and convert audio
            print("   -> Loading audio file...")
            audio_data = self._load_and_convert_audio(file_path, clean_wav_path)
            
            # Step 2: Diarize (identify speakers)
            print("   -> Running Diarization...")
            segments = self._diarize_and_filter(audio_data)
            
            # Step 3: Remap speaker IDs to sequential
            speaker_id_map = self._remap_speaker_ids(segments)
            
            # Step 4: Transcribe all segments
            print(f"   -> Found {len(segments)} segments. Transcribing...")
            raw_segments = self._transcribe_segments(segments, speaker_id_map, audio_data)
            
            # Step 5: Add punctuation (batch mode for efficiency)
            print(f"   -> Adding punctuation to {len(raw_segments)} segments (batch mode)...")
            formatted_segments = self._add_punctuation_batch(raw_segments)
            
            # Step 6: Format final output
            full_transcript, output_segments = self._format_output(formatted_segments)
            
            elapsed = time.time() - start_time
            print(f"   -> Transcription complete in {elapsed:.2f}s")
            
            return {
                "status": "success",
                "text": full_transcript,
                "segments": output_segments,
                "processing_time": elapsed
            }
        
        except (AudioProcessingError, TranscriptionError):
            raise
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise AudioProcessingError(f"Audio processing failed: {e}") from e
        
        finally:
            # Always clean up temporary files
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(clean_wav_path):
                os.remove(clean_wav_path)
    
    def _load_and_convert_audio(self, input_path: str, output_path: str) -> np.ndarray:
        """
        Load audio file and convert to target sample rate with preprocessing.
        
        Applies noise reduction and normalization if enabled in config to improve
        diarization and transcription quality, especially for microphone recordings.
        
        Args:
            input_path: Path to input audio file
            output_path: Path to save converted WAV file
        
        Returns:
            np.ndarray: Audio data as float32 array
        
        Raises:
            AudioProcessingError: If audio loading fails
        """
        try:
            # Load audio and resample to 16kHz (required by ASR model)
            audio, sr = librosa.load(input_path, sr=AudioConfig.SAMPLE_RATE)
            
            print(f"   -> Original audio: {len(audio)/sr:.2f}s, {sr}Hz")
            
            # Apply audio preprocessing for better quality
            if AudioConfig.ENABLE_NOISE_REDUCTION:
                try:
                    import noisereduce as nr
                    audio = nr.reduce_noise(y=audio, sr=sr, stationary=True)
                    print("   -> Applied noise reduction")
                except ImportError:
                    print("   -> Skipping noise reduction (noisereduce not installed)")
            
            if AudioConfig.ENABLE_NORMALIZATION:
                # Normalize volume to consistent level
                audio = librosa.util.normalize(audio)
                print("   -> Applied volume normalization")
            
            # Remove leading/trailing silence (helps with segmentation)
            audio, _ = librosa.effects.trim(audio, top_db=20)
            print(f"   -> Trimmed audio: {len(audio)/sr:.2f}s")
            
            # Save as clean WAV for consistency
            sf.write(output_path, audio, AudioConfig.SAMPLE_RATE)
            
            return audio.astype(np.float32)
        except AudioProcessingError:
            raise
        except Exception as e:
            raise AudioProcessingError(f"Failed to load audio: {e}") from e
    
    def _diarize_and_filter(self, audio_data: np.ndarray) -> List:
        """
        Perform diarization and filter short segments.
        
        Args:
            audio_data: Audio waveform data
        
        Returns:
            List of filtered diarization segments
        """
        # Run diarization
        all_segments = self.asr_service.diarize_audio(audio_data)
        
        # Debug logging: show raw diarization output
        if AudioConfig.ENABLE_DEBUG_LOGGING:
            print(f"\n{'='*60}")
            print(f"RAW DIARIZATION OUTPUT")
            print(f"{'='*60}")
            print(f"Total segments detected: {len(all_segments)}")
            print(f"\nFirst 20 segments:")
            for i, seg in enumerate(all_segments[:20]):
                duration = seg.end - seg.start
                print(f"  [{i:2d}] Speaker_{seg.speaker}: {seg.start:6.2f}s - {seg.end:6.2f}s (duration: {duration:5.2f}s)")
            
            # Show speaker distribution
            from collections import Counter
            speaker_counts = Counter(seg.speaker for seg in all_segments)
            print(f"\nSpeaker distribution:")
            for speaker_id, count in sorted(speaker_counts.items()):
                print(f"  Speaker_{speaker_id}: {count} segments")
            print(f"{'='*60}\n")
        
        # Filter out very short segments (likely noise or false detections)
        min_duration = AudioConfig.MIN_SEGMENT_DURATION
        segments = [seg for seg in all_segments if (seg.end - seg.start) >= min_duration]
        
        print(f"   -> Filtered segments: {len(all_segments)} → {len(segments)} (removed segments < {min_duration}s)")
        
        # Merge adjacent segments from same speaker (helps with over-segmentation)
        from medical_api.config import DiarizationConfig
        if DiarizationConfig.MERGE_GAP_THRESHOLD > 0:
            merged_segments = self._merge_adjacent_same_speaker(segments)
            if len(merged_segments) < len(segments):
                print(f"   -> Merged segments: {len(segments)} → {len(merged_segments)} (merged adjacent same-speaker segments)")
            segments = merged_segments
        
        return segments
    
    def _merge_adjacent_same_speaker(self, segments: List) -> List:
        """
        Merge consecutive segments from same speaker if gap is small.
        
        This helps fix over-segmentation where one person is incorrectly
        split into multiple speaker IDs due to pauses or voice changes.
        
        Args:
            segments: List of diarization segments
        
        Returns:
            List of merged segments
        """
        if len(segments) <= 1:
            return segments
        
        from medical_api.config import DiarizationConfig
        max_gap = DiarizationConfig.MERGE_GAP_THRESHOLD
        
        merged = []
        current_segment = None
        
        for seg in segments:
            if current_segment is None:
                # First segment, create a copy
                current_segment = type('Segment', (), {
                    'speaker': seg.speaker,
                    'start': seg.start,
                    'end': seg.end
                })()
            elif (seg.speaker == current_segment.speaker and 
                  seg.start - current_segment.end < max_gap):
                # Same speaker and small gap - extend current segment
                current_segment.end = seg.end
            else:
                # Different speaker or large gap - save current and start new
                merged.append(current_segment)
                current_segment = type('Segment', (), {
                    'speaker': seg.speaker,
                    'start': seg.start,
                    'end': seg.end
                })()
        
        # Don't forget the last segment
        if current_segment is not None:
            merged.append(current_segment)
        
        return merged
    
    def _remap_speaker_ids(self, segments: List) -> Dict[int, int]:
        """
        Remap speaker IDs to sequential numbers (0, 1, 2...).
        
        After filtering noise segments, speaker IDs may have gaps (e.g., 0, 5, 97).
        This function creates a mapping to sequential IDs for cleaner output.
        
        Args:
            segments: List of diarization segments
        
        Returns:
            Dict mapping original speaker IDs to sequential IDs
        """
        unique_speakers = sorted(set(seg.speaker for seg in segments))
        speaker_id_map = {old_id: new_id for new_id, old_id in enumerate(unique_speakers)}
        
        print(f"   -> Speaker remapping: {len(unique_speakers)} unique speakers")
        if len(unique_speakers) <= 10:
            print(f"      Original IDs: {unique_speakers}")
        else:
            print(f"      Original IDs: {unique_speakers[:10]}... (showing first 10)")
        print(f"      Remapped to: Speaker_0 to Speaker_{len(unique_speakers)-1}")
        
        return speaker_id_map
    
    def _transcribe_segments(
        self,
        segments: List,
        speaker_id_map: Dict[int, int],
        audio_data: np.ndarray
    ) -> List[Dict]:
        """
        Transcribe all segments and collect raw texts.
        
        Args:
            segments: Diarization segments
            speaker_id_map: Speaker ID remapping dictionary
            audio_data: Full audio waveform
        
        Returns:
            List of dictionaries with segment data and raw transcriptions
        """
        raw_segments = []
        
        for seg in segments:
            # Use remapped speaker ID (sequential: 0, 1, 2, 3...)
            remapped_speaker_id = speaker_id_map[seg.speaker]
            speaker_label = f"Speaker_{remapped_speaker_id}"
            
            # Extract audio segment
            start_idx = int(seg.start * AudioConfig.SAMPLE_RATE)
            end_idx = int(seg.end * AudioConfig.SAMPLE_RATE)
            
            # Ensure we don't exceed audio bounds
            if end_idx > len(audio_data):
                end_idx = len(audio_data)
            
            segment_audio = audio_data[start_idx:end_idx]
            
            # Transcribe segment
            raw_text = self.asr_service.transcribe_segment(segment_audio)
            
            if raw_text:
                raw_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "speaker": speaker_label,
                    "raw_text": raw_text
                })
        
        return raw_segments
    
    def _add_punctuation_batch(self, raw_segments: List[Dict]) -> List[Dict]:
        """
        Add punctuation to all segments in batch (more efficient).
        
        Args:
            raw_segments: Segments with raw transcription text
        
        Returns:
            Segments with punctuated text
        """
        if not raw_segments:
            return []
        
        # Extract all raw texts
        raw_texts = [seg["raw_text"] for seg in raw_segments]
        
        # Batch punctuation processing (faster than one-by-one)
        punctuated_texts = self.vibert_service.add_punctuation_batch(raw_texts)
        
        # Combine with segment metadata
        formatted_segments = []
        for seg_data, punctuated_text in zip(raw_segments, punctuated_texts):
            formatted_segments.append({
                "start": seg_data["start"],
                "end": seg_data["end"],
                "speaker": seg_data["speaker"],
                "text": punctuated_text
            })
        
        return formatted_segments
    
    def _format_output(self, segments: List[Dict]) -> tuple:
        """
        Format segments into full transcript and structured output.
        
        Args:
            segments: Segments with punctuated text
        
        Returns:
            Tuple of (full_transcript_string, list_of_segment_dicts)
        """
        full_transcript = ""
        output_segments = []
        
        for seg in segments:
            # Format timestamp as HH:MM:SS
            timestamp = time.strftime('%H:%M:%S', time.gmtime(seg["start"]))
            line = f"[{timestamp}] {seg['speaker']}: {seg['text']}"
            full_transcript += line + "\n"
            
            output_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "speaker": seg["speaker"],
                "text": seg["text"]
            })
        
        return full_transcript, output_segments
