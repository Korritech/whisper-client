import asyncio

import pytest

from whisper_client.__main__ import run


@pytest.fixture(autouse=True)
def no_sound(monkeypatch):
    async def silent(sound):
        pass

    monkeypatch.setattr("whisper_client.__main__.play", silent, raising=False)


async def settle():
    """Lets the other tasks run until they are all waiting."""
    for _ in range(10):
        await asyncio.sleep(0)


class FakeTranscriber:
    """Stands in for the mic and the server; finishes when `done` is set."""

    def __init__(self, text="Bonjour"):
        self.text = text
        self.calls = 0
        self.done = asyncio.Event()
        self.done.set()

    async def __call__(self, stop_event):
        self.calls += 1
        await stop_event.wait()
        await self.done.wait()
        return self.text


async def start(transcriber, min_press=0, finish_timeout=5):
    events, delivered = asyncio.Queue(), []

    async def deliver(text):
        delivered.append(text)

    task = asyncio.create_task(
        run(events, transcriber, deliver, min_press, finish_timeout)
    )
    return events, delivered, task


async def stop(task):
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


@pytest.mark.asyncio
async def test_delivers_the_text_after_release():
    transcriber = FakeTranscriber()
    events, delivered, task = await start(transcriber)

    events.put_nowait(("press", 0.0))
    await settle()
    assert delivered == []

    events.put_nowait(("release", 1.0))
    await settle()
    assert delivered == ["Bonjour"]
    await stop(task)


@pytest.mark.asyncio
async def test_chains_several_dictations():
    transcriber = FakeTranscriber()
    events, delivered, task = await start(transcriber)

    for _ in range(3):
        events.put_nowait(("press", 0.0))
        await settle()
        events.put_nowait(("release", 1.0))
        await settle()

    assert delivered == ["Bonjour"] * 3
    await stop(task)


@pytest.mark.asyncio
async def test_empty_text_is_not_delivered():
    transcriber = FakeTranscriber(text="")
    events, delivered, task = await start(transcriber)

    events.put_nowait(("press", 0.0))
    await settle()
    events.put_nowait(("release", 1.0))
    await settle()

    assert delivered == []
    await stop(task)


@pytest.mark.asyncio
async def test_short_press_cancels_the_dictation():
    cancelled = []

    async def transcriber(stop_event):
        try:
            await stop_event.wait()
            return "Merci."
        except asyncio.CancelledError:
            cancelled.append(True)
            raise

    events, delivered, task = await start(transcriber, min_press=10)

    events.put_nowait(("press", 0.0))
    await settle()
    events.put_nowait(("release", 1.0))
    await settle()

    assert cancelled == [True]
    assert delivered == []
    assert not task.done()
    await stop(task)


@pytest.mark.asyncio
async def test_a_silent_server_does_not_block_the_next_dictation():
    calls = []

    async def transcriber(stop_event):
        calls.append(True)
        await stop_event.wait()
        if len(calls) == 1:
            await asyncio.Event().wait()  # never finishes
        return "Bonjour"

    events, delivered, task = await start(transcriber, finish_timeout=0.01)

    events.put_nowait(("press", 0.0))
    await settle()
    events.put_nowait(("release", 1.0))
    await asyncio.sleep(0.05)

    events.put_nowait(("press", 2.0))
    await settle()
    events.put_nowait(("release", 3.0))
    await settle()

    assert delivered == ["Bonjour"]
    await stop(task)


@pytest.mark.asyncio
async def test_survives_a_failed_dictation():
    calls = []

    async def transcriber(stop_event):
        calls.append(True)
        await stop_event.wait()
        if len(calls) == 1:
            raise ConnectionRefusedError("server is down")
        return "Bonjour"

    events, delivered, task = await start(transcriber)

    for _ in range(2):
        events.put_nowait(("press", 0.0))
        await settle()
        events.put_nowait(("release", 1.0))
        await settle()

    assert delivered == ["Bonjour"]
    await stop(task)


@pytest.mark.asyncio
async def test_press_during_processing_is_ignored():
    transcriber = FakeTranscriber()
    transcriber.done.clear()
    events, delivered, task = await start(transcriber)

    events.put_nowait(("press", 0.0))
    await settle()
    events.put_nowait(("release", 1.0))
    await settle()

    # the text is still being processed: this press must not start a dictation
    events.put_nowait(("press", 0.0))
    events.put_nowait(("release", 1.0))
    await settle()
    transcriber.done.set()
    await settle()

    assert delivered == ["Bonjour"]
    assert transcriber.calls == 1
    await stop(task)
