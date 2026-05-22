from pydantic import BaseModel


class TranscriptionRequest(BaseModel):
    audio_base64: str
    sample_rate: int = 16000


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float


class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


class TranslationResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str


class TTSRequest(BaseModel):
    text: str
    language: str
    voice: str | None = None


class TTSResponse(BaseModel):
    audio_base64: str
    mime_type: str = "audio/wav"


class TranslateAudioRequest(BaseModel):
    audio_base64: str
    sample_rate: int = 16000


class TranslateAudioResponse(BaseModel):
    original_text: str
    detected_language: str
    translated_text: str
    target_language: str
    audio_base64: str
    mime_type: str = "audio/wav"


class ErrorResponse(BaseModel):
    error: str
    detected_language: str | None = None
    original_text: str | None = None
