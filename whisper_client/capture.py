import asyncio
import pyaudio
import logging

from whisper_client.config import SAMPLE_RATE, CHUNK_SIZE

log = logging.getLogger(__name__)

async def mic_chunks(stop_event: asyncio.Event):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def callback(in_data, frame_count, time_info, status):
        loop.call_soon_threadsafe(queue.put_nowait, in_data)
        return (None, pyaudio.paContinue)

    async def wait_for_stop():
        await stop_event.wait()
        stream.stop_stream()
        loop.call_soon(queue.put_nowait, None)

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        stream_callback=callback
    )
    stopper = asyncio.create_task(wait_for_stop())

    log.info("Start audio capture...")
    try:
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    finally:
        stopper.cancel()
        stream.stop_stream()
        stream.close()
        audio.terminate()
