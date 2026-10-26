"""Optional offline speech-to-text. Typed notes always work; ASR is plugged in if installed.

Backends (first available wins):
  1. faster-whisper  (pip install faster-whisper; model cached locally after first download)
  2. vosk            (pip install vosk; set VOSK_MODEL_PATH to a downloaded model folder)
"""
from __future__ import annotations
import json
import wave

from . import config


class AsrUnavailable(RuntimeError):
    pass


def available_backends() -> list[str]:
    found = []
    try:
        import faster_whisper  # noqa: F401
        found.append("faster-whisper")
    except Exception:
        pass
    try:
        import vosk  # noqa: F401
        if config.VOSK_MODEL_PATH:
            found.append("vosk")
    except Exception:
        pass
    return found


_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    return _whisper_model


def transcribe(audio_path: str) -> str:
    backends = available_backends()
    if "faster-whisper" in backends:
        model = _get_whisper_model()
        segments, _ = model.transcribe(audio_path, language="en", vad_filter=True,
                                       initial_prompt="Medications and procedures: epinephrine, aspirin, morphine, "
                                                      "IV, IM, intubated, defibrillated, normal saline.")
        return " ".join(s.text.strip() for s in segments).strip()
    if "vosk" in backends:
        import vosk
        wf = wave.open(audio_path, "rb")
        rec = vosk.KaldiRecognizer(vosk.Model(config.VOSK_MODEL_PATH), wf.getframerate())
        parts = []
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                parts.append(json.loads(rec.Result()).get("text", ""))
        parts.append(json.loads(rec.FinalResult()).get("text", ""))
        return " ".join(p for p in parts if p).strip()
    raise AsrUnavailable("No offline ASR backend installed. Type the note, or install faster-whisper / vosk "
                         "(see README). Typed input works without any ASR.")
