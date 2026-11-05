import asyncio
import json

import pytest
from websockets.asyncio.server import serve

from whisper_client.session import dictate


def result(text, is_partial):
    return json.dumps({"is_partial": is_partial, "data": {"text": text}, "time": 1.0})


class FakeServer:
    """Records what the client sends, then replays scripted results on stop."""

    def __init__(self, replies):
        self.replies = replies
        self.received = []

    async def handler(self, websocket):
        async for message in websocket:
            self.received.append(message)
            if isinstance(message, str) and json.loads(message)["type"] == "stop":
                for reply in self.replies:
                    await websocket.send(reply)
                await websocket.close()


async def run_dictation(replies, chunks):
    fake = FakeServer(replies)
    async with serve(fake.handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        text = await asyncio.wait_for(dictate(chunks, f"ws://127.0.0.1:{port}"), 5)
    return text, fake.received


async def audio(*frames):
    for frame in frames:
        yield frame


@pytest.mark.asyncio
async def test_sends_start_then_audio_then_stop():
    _, received = await run_dictation([], audio(b"aa", b"bb"))

    assert json.loads(received[0])["type"] == "start"
    assert received[1:3] == [b"aa", b"bb"]
    assert json.loads(received[3]) == {"type": "stop"}


@pytest.mark.asyncio
async def test_start_frame_carries_the_chosen_settings():
    fake = FakeServer([])
    async with serve(fake.handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        await asyncio.wait_for(
            dictate(
                audio(b"aa"),
                f"ws://127.0.0.1:{port}",
                model="tiny.en.pt",
                language="en",
                prompt="Hello. AWS.",
            ),
            5,
        )

    start = json.loads(fake.received[0])
    assert start == {
        "type": "start",
        "model": "tiny.en.pt",
        "language": "en",
        "prompt": "Hello. AWS.",
    }


@pytest.mark.asyncio
async def test_joins_finals_and_ignores_partials():
    replies = [
        result(" Bonjour", True),
        result(" Bonjour à tous.", False),
        result(" Comment", True),
        result(" Comment ça va ?", False),
    ]

    text, _ = await run_dictation(replies, audio(b"aa"))

    assert text == "Bonjour à tous. Comment ça va ?"


@pytest.mark.asyncio
async def test_server_error_message_does_not_stop_the_dictation():
    replies = [
        json.dumps({"type": "error", "message": "invalid control"}),
        result(" Merci.", False),
    ]

    text, _ = await run_dictation(replies, audio(b"aa"))

    assert text == "Merci."


@pytest.mark.asyncio
async def test_silence_gives_an_empty_text():
    text, _ = await run_dictation([], audio(b"aa"))

    assert text == ""


@pytest.mark.asyncio
async def test_closes_the_audio_source_when_the_server_drops():
    closed = []

    async def endless_audio():
        try:
            while True:
                yield b"aa"
                await asyncio.sleep(0.01)
        finally:
            closed.append(True)

    async def dropping_handler(websocket):
        await websocket.recv()
        await websocket.recv()
        await websocket.close(code=1011)

    async with serve(dropping_handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        with pytest.raises(Exception):
            await asyncio.wait_for(dictate(endless_audio(), f"ws://127.0.0.1:{port}"), 5)

    assert closed == [True]
