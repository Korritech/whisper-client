import os
from pathlib import Path

# Serveur
HTTP_URL = "http://127.0.0.1:8181"
WS_URL = "ws://127.0.0.1:8181/ws"
PROTOCOL_VERSION = 1
SERVER_DIR = Path(
    os.environ.get("WHISPER_FLOW_DIR", Path(__file__).resolve().parents[2] / "whisper-flow")
)
START_TIMEOUT = 120
STOP_TIMEOUT = 5

# Transcription
MODEL = "small.pt"
LANGUAGE = "fr"
PROMPT = "Je développe avec Claude Code en Python, avec asyncio et des WebSocket."

# Dictée
MIN_PRESS = 0.2
FINISH_TIMEOUT = 30

# Audio
SAMPLE_RATE=16000
CHUNK_SIZE=1024

# Logs
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
