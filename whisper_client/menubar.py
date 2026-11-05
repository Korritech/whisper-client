import asyncio
import threading

import rumps

from whisper_client import status

ICONS = {
    status.STARTING: "⚪",
    status.READY: "🟢",
    status.RECORDING: "🔴",
    status.TRANSCRIBING: "🟠",
    status.ERROR: "⚠️",
}


class Backend:
    """Runs the asyncio part in its own thread."""

    def __init__(self, main):
        self.main = main

    def start(self):
        self.thread = threading.Thread(target=asyncio.run, args=(self._run(),))
        self.thread.start()

    async def _run(self):
        self.loop = asyncio.get_running_loop()
        self.task = asyncio.current_task()
        try:
            await self.main()
        except BaseException:
            status.set(status.ERROR)
            raise

    def stop(self):
        self.loop.call_soon_threadsafe(self.task.cancel)
        self.thread.join(timeout=10)

class App(rumps.App):
    def __init__(self, backend):
        super().__init__(ICONS[status.STARTING], quit_button=None)
        self.backend = backend
        self.menu = ["Quitter"]

    @rumps.timer(0.2)
    def refresh(self, _):
        self.title = ICONS[status.current]

    @rumps.clicked("Quitter")
    def quit(self, _):
        self.backend.stop()
        rumps.quit_application()
