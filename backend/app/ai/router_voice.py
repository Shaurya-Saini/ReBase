"""E24 /voice/tts, E25 /translate (Sarvam proxy). Stubbed (B0) — real in B12."""

from fastapi import APIRouter
from fastapi.responses import Response

from app.errors import ApiError
from app.schemas import TranslateRequest, TranslateResponse, TtsRequest

router = APIRouter(tags=["voice"])


@router.post(
    "/voice/tts",
    response_class=Response,
    responses={200: {"content": {"audio/wav": {}}}},
)
def tts(body: TtsRequest):
    # TODO B12: app.ai.sarvam.tts -> Response(content=wav, media_type="audio/wav")
    raise ApiError(503, "UPSTREAM_UNAVAILABLE", "TTS not implemented yet — use on-device TTS")


@router.post("/translate", response_model=TranslateResponse)
def translate(body: TranslateRequest):
    # TODO B12: app.ai.sarvam.translate. Stub echoes the input text.
    return {"text": body.text, "lang": body.target}
