"""
Voice: TTS Provider Abstraction for Writers Room

Supports multiple TTS providers with automatic fallback:
- OpenAI TTS (reliable, $0.015/1K chars)
- ElevenLabs (best quality, free tier 10K chars/month)
- pyttsx3 (free, local, offline fallback)
"""

import os
import base64
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class VoiceProvider(Enum):
    """Available TTS providers."""
    OPENAI = "openai"
    ELEVENLABS = "elevenlabs"
    PYTTSX3 = "pyttsx3"


@dataclass
class VoiceConfig:
    """Configuration for a voice assignment."""
    provider: VoiceProvider
    voice_id: str
    name: str
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "provider": self.provider.value,
            "voice_id": self.voice_id,
            "name": self.name,
            "description": self.description
        }


# Agent voice assignments
AGENT_VOICES = {
    "Rod Serling": VoiceConfig(
        provider=VoiceProvider.OPENAI,
        voice_id="onyx",
        name="Onyx",
        description="Deep, authoritative male voice - perfect for Twilight Zone narration"
    ),
    "Stephen King": VoiceConfig(
        provider=VoiceProvider.OPENAI,
        voice_id="echo",
        name="Echo",
        description="Natural male voice with warmth - conversational horror"
    ),
    "H.P. Lovecraft": VoiceConfig(
        provider=VoiceProvider.OPENAI,
        voice_id="fable",
        name="Fable",
        description="Expressive, dramatic voice - scholarly cosmic horror"
    ),
    "Jorge Luis Borges": VoiceConfig(
        provider=VoiceProvider.OPENAI,
        voice_id="alloy",
        name="Alloy",
        description="Neutral, thoughtful voice - philosophical musings"
    ),
    "Robert Stack": VoiceConfig(
        provider=VoiceProvider.OPENAI,
        voice_id="onyx",
        name="Onyx",
        description="Deep, measured male voice - mystery narration"
    ),
    "RIP Tequila Bot": VoiceConfig(
        provider=VoiceProvider.OPENAI,
        voice_id="shimmer",
        name="Shimmer",
        description="Energetic voice - enthusiastic marketing"
    ),
    "The Producer": VoiceConfig(
        provider=VoiceProvider.OPENAI,
        voice_id="nova",
        name="Nova",
        description="Authoritative female voice - Hollywood executive"
    )
}

# ElevenLabs voice mappings (if user has API key)
ELEVENLABS_VOICES = {
    "Rod Serling": "21m00Tcm4TlvDq8ikWAM",  # Rachel - deep narrator
    "Stephen King": "AZnzlk1XvdvUeBnXmlld",  # Domi - natural
    "H.P. Lovecraft": "ErXwobaYiN019PkySvjV",  # Antoni - dramatic
    "Jorge Luis Borges": "VR6AewLTigWG4xSOukaG",  # Arnold - thoughtful
    "Robert Stack": "pNInz6obpgDQGcFmaJgB",  # Adam - deep
    "RIP Tequila Bot": "EXAVITQu4vr4xnSDxMaL",  # Bella - energetic
    "The Producer": "21m00Tcm4TlvDq8ikWAM"   # Rachel - authoritative
}


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def generate_audio(self, text: str, voice_id: str) -> Optional[Tuple[bytes, str]]:
        """Generate audio from text. Returns (audio bytes, mime type) or None on failure."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (API key set, library installed)."""
        pass


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS provider using their text-to-speech API."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client = None

    def is_available(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate_audio(self, text: str, voice_id: str) -> Optional[Tuple[bytes, str]]:
        if not self.is_available():
            return None

        try:
            client = self._get_client()
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice_id,
                input=text
            )
            return response.content, "audio/mpeg"
        except Exception as e:
            print(f"OpenAI TTS error: {e}")
            return None


class ElevenLabsTTSProvider(TTSProvider):
    """ElevenLabs TTS provider for highest quality voice synthesis."""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import elevenlabs
            return True
        except ImportError:
            return False

    def generate_audio(self, text: str, voice_id: str) -> Optional[Tuple[bytes, str]]:
        if not self.is_available():
            return None

        try:
            from elevenlabs import generate, set_api_key
            set_api_key(self.api_key)

            audio = generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            return audio, "audio/mpeg"
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return None


class Pyttsx3TTSProvider(TTSProvider):
    """Local TTS using pyttsx3 - free, offline fallback."""

    def __init__(self):
        self._engine = None

    def is_available(self) -> bool:
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def _get_engine(self):
        if self._engine is None:
            import pyttsx3
            self._engine = pyttsx3.init()
        return self._engine

    def generate_audio(self, text: str, voice_id: str) -> Optional[Tuple[bytes, str]]:
        if not self.is_available():
            return None

        try:
            import tempfile
            import pyttsx3

            engine = self._get_engine()

            # Set voice properties based on voice_id hints
            voices = engine.getProperty('voices')
            if voices:
                # Try to match voice_id to available system voices
                for voice in voices:
                    if voice_id.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break

            # Generate to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name

            engine.save_to_file(text, temp_path)
            engine.runAndWait()

            # Read the file
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()

            # Clean up
            os.unlink(temp_path)

            return audio_bytes, "audio/wav"
        except Exception as e:
            print(f"pyttsx3 TTS error: {e}")
            return None


class VoiceManager:
    """
    Manages TTS generation with automatic provider fallback.

    Priority: ElevenLabs > OpenAI > pyttsx3
    """

    def __init__(self, preferred_provider: Optional[VoiceProvider] = None):
        self.providers = {
            VoiceProvider.OPENAI: OpenAITTSProvider(),
            VoiceProvider.ELEVENLABS: ElevenLabsTTSProvider(),
            VoiceProvider.PYTTSX3: Pyttsx3TTSProvider()
        }
        self.preferred_provider = preferred_provider
        self._voice_enabled = True

    def set_enabled(self, enabled: bool):
        """Enable or disable voice generation."""
        self._voice_enabled = enabled

    def is_enabled(self) -> bool:
        """Check if voice is enabled."""
        return self._voice_enabled

    def get_available_providers(self) -> list:
        """Get list of available providers."""
        return [p for p, provider in self.providers.items() if provider.is_available()]

    def get_agent_voice(self, agent_name: str) -> VoiceConfig:
        """Get the voice configuration for an agent."""
        return AGENT_VOICES.get(agent_name, VoiceConfig(
            provider=VoiceProvider.OPENAI,
            voice_id="alloy",
            name="Alloy",
            description="Default voice"
        ))

    def generate_audio(self, text: str, agent_name: str, voice_id_override: Optional[str] = None) -> Optional[Tuple[bytes, str]]:
        """
        Generate audio for an agent's text.

        Automatically selects the best available provider.
        """
        if not self._voice_enabled:
            return None

        voice_config = self.get_agent_voice(agent_name)

        # Determine provider priority
        if self.preferred_provider and self.preferred_provider in self.providers:
            provider_order = [self.preferred_provider]
        else:
            # Default priority: ElevenLabs > OpenAI > pyttsx3
            provider_order = [
                VoiceProvider.ELEVENLABS,
                VoiceProvider.OPENAI,
                VoiceProvider.PYTTSX3
            ]

        # Add remaining providers as fallbacks
        for p in VoiceProvider:
            if p not in provider_order:
                provider_order.append(p)

        # Try each provider
        for provider_type in provider_order:
            provider = self.providers.get(provider_type)
            if provider and provider.is_available():
                # Get appropriate voice ID for this provider
                if provider_type == VoiceProvider.ELEVENLABS:
                    voice_id = ELEVENLABS_VOICES.get(agent_name, "21m00Tcm4TlvDq8ikWAM")
                else:
                    voice_id = voice_id_override or voice_config.voice_id

                audio = provider.generate_audio(text, voice_id)
                if audio:
                    return audio

        return None

    def generate_audio_base64(self, text: str, agent_name: str, voice_id_override: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """Generate audio and return (base64, mime) for web transport."""
        audio = self.generate_audio(text, agent_name, voice_id_override=voice_id_override)
        if audio:
            audio_bytes, mime_type = audio
            return base64.b64encode(audio_bytes).decode('utf-8'), mime_type
        return None


# Global instance for convenience
_voice_manager: Optional[VoiceManager] = None


def get_voice_manager() -> VoiceManager:
    """Get or create the global VoiceManager instance."""
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceManager()
    return _voice_manager


def generate_agent_audio(text: str, agent_name: str, voice_id_override: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Convenience function to generate audio for an agent.

    Returns (base64-encoded audio, mime type) or None.
    """
    return get_voice_manager().generate_audio_base64(text, agent_name, voice_id_override=voice_id_override)
