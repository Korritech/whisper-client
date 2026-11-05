STARTING = "starting"
READY = "ready"
RECORDING = "recording"
TRANSCRIBING = "transcribing"
ERROR = "error"

current = STARTING


def set(value):
    global current
    current = value
