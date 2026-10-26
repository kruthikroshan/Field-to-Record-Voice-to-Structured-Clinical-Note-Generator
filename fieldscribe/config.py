"""Runtime configuration (all via environment variables, with offline-safe defaults)."""
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("FIELDSCRIBE_DATA", Path(__file__).resolve().parent.parent / "data"))
INCIDENT_DIR = DATA_DIR / "incidents"
MOCK_EHR_DIR = DATA_DIR / "mock_ehr"
SYNC_URL = os.environ.get("FIELDSCRIBE_SYNC_URL")        # hospital endpoint; unset = stay queued
VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH")      # optional offline ASR model dir
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base.en")  # faster-whisper model name or path

LOW_CONFIDENCE = 0.70
