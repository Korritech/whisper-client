from pynput import keyboard
import time

HOTKEY = keyboard.Key.alt_r



def start_listener(loop, events):
    def on_press(key):
        if(key == HOTKEY):
            loop.call_soon_threadsafe(events.put_nowait, ("press", time.monotonic()))


    def on_release(key):
        if(key == HOTKEY):
            loop.call_soon_threadsafe(events.put_nowait, ("release", time.monotonic()))

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    return listener
