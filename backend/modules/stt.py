"""
Speech-to-Text using Fast Whisper with CUDA support.
"""

import os
from faster_whisper import WhisperModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class STTService:
    def __init__(self, model_size: str = "base", device: str = "cuda", compute_type: str = "float16"):
        """
        Initialize Fast Whisper model.
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to use (cuda, cpu)
            compute_type: Compute type (float16, int8, int8_float16)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        
        logger.info(f"Initializing Whisper model: {model_size} on {device}")
    
    def load_model(self):
        """Load the Whisper model (lazy loading)."""
        if self.model is None:
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                # Fallback to CPU if CUDA fails
                if self.device == "cuda":
                    logger.warning("Falling back to CPU")
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self.model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type
                    )
    
    def transcribe(self, audio_path: str, language: str = "pt") -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (pt, en, etc.)
        
        Returns:
            Transcribed text
        """
        self.load_model()
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Combine all segments
            transcription = " ".join([segment.text for segment in segments])
            
            logger.info(f"Transcription completed: {len(transcription)} characters")
            logger.debug(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            
            return transcription.strip()
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    def transcribe_with_timestamps(self, audio_path: str, language: str = "pt") -> list:
        """
        Transcribe audio with word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            language: Language code
        
        Returns:
            List of segments with timestamps
        """
        self.load_model()
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True
            )
            
            result = []
            for segment in segments:
                result.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error transcribing with timestamps: {e}")
            raise
