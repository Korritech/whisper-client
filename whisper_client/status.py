STARTING = "starting"
READY = "ready"
RECORDING = "recording"
TRANSCRIBING = "transcribing"
ERROR = "error"

current = STARTING
models = []


def set(value):
    global current
    current = value
