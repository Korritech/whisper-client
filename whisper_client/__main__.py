import asyncio
import logging
import os
from whisper_client.capture import mic_chunks
from whisper_client.session import dictate
from whisper_client.hotkey import start_listener
from whisper_client.inject import inject
from whisper_client.sounds import START, STOP, ERROR, play
from whisper_client.server import managed_server, check_server, get_models
from whisper_client import status
from whisper_client.menubar import Backend, App
from whisper_client.settings import load

from whisper_client.config import FINISH_TIMEOUT, LOG_LEVEL, MIN_PRESS

log = logging.getLogger(__name__)
settings = load()

async def wait_for(events, expected):
    while True:
        kind, when = await events.get()
        if kind == expected:
            return when


def transcribe(stop_event):
    return dictate(
        mic_chunks(stop_event),
        model=settings.model,
        language=settings.language,
        prompt=settings.prompt()
    )

async def run(events, transcribe, deliver, min_press=MIN_PRESS, finish_timeout=FINISH_TIMEOUT):
    while True:
        debut = await wait_for(events, "press")
        status.set(status.RECORDING)
        await play(START)

        stop_event = asyncio.Event()
        task = asyncio.create_task(transcribe(stop_event))

        fin = await wait_for(events, "release")
        # Cancel capture if press time is < min press time
        duree = fin - debut;
        if(duree <= min_press):
            status.set(status.READY)
            task.cancel()
            await asyncio.wait([task])
            continue

        stop_event.set()
        status.set(status.TRANSCRIBING)
        await play(STOP)
        try:
            async with asyncio.timeout(finish_timeout):
                text = await task
                status.set(status.READY)
        except Exception as e:
            log.exception("Dictée échouée")
            status.set(status.ERROR)
            await play(ERROR)
            text = ""

        if text:
            await deliver(text)

        while not events.empty():
            events.get_nowait()


async def main():
    async with managed_server():
        await check_server()
        models = await get_models()
        log.info(f"models {models}")
        status.models = models

        status.set(status.READY)

        event_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        listener = start_listener(loop, event_queue)
        try:
            await run(event_queue, transcribe, inject)
        finally:
            listener.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", LOG_LEVEL),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    backend = Backend(main)
    backend.start()
    App(backend, settings).run()

#    asyncio.run(main())
