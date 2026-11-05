import asyncio
import threading

import rumps
from pynput import keyboard

state = {"title": "⚪"}


async def blink():
    while True:
        await asyncio.sleep(1)
        if state["title"] != "🔴":
            state["title"] = "🟢" if state["title"] == "⚪" else "⚪"


def on_press(key):
    print("press", key, flush=True)
    if key == keyboard.Key.alt_r:
        state["title"] = "🔴"


def on_release(key):
    print("release", key, flush=True)
    if key == keyboard.Key.alt_r:
        state["title"] = "⚪"


class App(rumps.App):
    @rumps.timer(0.2)
    def refresh(self, _):
        self.title = state["title"]

    @rumps.clicked("Test")
    def test(self, _):
        print("clic", flush=True)


loop = asyncio.new_event_loop()
threading.Thread(target=loop.run_forever, daemon=True).start()
asyncio.run_coroutine_threadsafe(blink(), loop)

keyboard.Listener(on_press=on_press, on_release=on_release).start()

App("⚪").run()
