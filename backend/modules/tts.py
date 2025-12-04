"""
Text-to-Speech using ElevenLabs with new API.
"""

import os
from elevenlabs.client import ElevenLabs
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_flash_v2_5",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ):
        """
        Initialize ElevenLabs TTS service with new API.
        
        Args:
            api_key: ElevenLabs API key
            voice_id: Voice ID to use
            model_id: Model ID (eleven_flash_v2_5, eleven_turbo_v2, etc.)
            stability: Voice stability (0.0-1.0)
            similarity_boost: Similarity boost (0.0-1.0)
            style: Style exaggeration (0.0-1.0)
            use_speaker_boost: Enable speaker boost
        """
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = model_id
        self.voice_settings = {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost
        }
        
        logger.info(f"TTS service initialized with voice: {voice_id}")
    
    def synthesize(self, text: str, output_path: Optional[str] = None) -> bytes:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            output_path: Optional path to save audio file
        
        Returns:
            Audio bytes
        """
        try:
            logger.info(f"Synthesizing text: {text[:50]}...")
            
            # Generate audio using new API
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                voice_settings=self.voice_settings
            )
            
            # Collect all audio chunks
            audio_bytes = b''.join(audio_generator)
            
            # Save to file if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                logger.info(f"Audio saved to: {output_path}")
            
            return audio_bytes
        
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            raise
    
    def synthesize_stream(self, text: str):
        """
        Synthesize text to speech with streaming.
        
        Args:
            text: Text to synthesize
        
        Yields:
            Audio chunks
        """
        try:
            logger.info(f"Streaming synthesis for: {text[:50]}...")
            
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                voice_settings=self.voice_settings
            )
            
            for chunk in audio_stream:
                yield chunk
        
        except Exception as e:
            logger.error(f"Error in streaming synthesis: {e}")
            raise
