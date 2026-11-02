import asyncio

from whisper_client.capture import mic_chunks
from whisper_client.session import dictate
from whisper_client.hotkey import start_listener
from whisper_client.inject import inject

MIN_PRESS = 0.2
FINISH_TIMEOUT = 30.

async def wait_for(events, expected):
    while True:
        kind, when = await events.get()
        if kind == expected:
            return when


def transcribe(stop_event):
    return dictate(mic_chunks(stop_event))

async def run(events, transcribe, deliver, min_press=MIN_PRESS, finish_timeout=FINISH_TIMEOUT):
    while True:
        debut = await wait_for(events, "press")

        stop_event = asyncio.Event()
        task = asyncio.create_task(transcribe(stop_event))

        fin = await wait_for(events, "release")
        # Cancel capture if press time is < min press time
        duree = fin - debut;
        if(duree <= min_press):
            task.cancel()
            await asyncio.wait([task])
            continue

        stop_event.set()

        try:
            async with asyncio.timeout(finish_timeout):
                text = await task
        except Exception as e:
            print("Dictée échouée :", repr(e))
            text = ""

        if text:
            await deliver(text)

        while not events.empty():
            events.get_nowait()

async def main():
    event_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    listener = start_listener(loop, event_queue)
    try:
        await run(event_queue, transcribe, inject)
    finally:
        listener.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
       print("Au revoir")
