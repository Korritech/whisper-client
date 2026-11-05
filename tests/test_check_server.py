import asyncio
import json
from contextlib import asynccontextmanager

import pytest

from whisper_client.server import PROTOCOL_VERSION, check_server
from whisper_client.session import MODEL


@asynccontextmanager
async def fake_ready(body, status="200 OK"):
    """A minimal HTTP server answering every request with `body`."""

    async def handle(reader, writer):
        await reader.readuntil(b"\r\n\r\n")
        payload = json.dumps(body).encode()
        headers = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n"
            f"Connection: close\r\n\r\n"
        )
        writer.write(headers.encode() + payload)
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        yield f"http://127.0.0.1:{port}"


@pytest.mark.asyncio
async def test_accepts_a_compatible_server():
    body = {"protocol_version": PROTOCOL_VERSION, "models": [MODEL]}

    async with fake_ready(body) as url:
        await check_server(url)


@pytest.mark.asyncio
async def test_exits_on_an_unknown_protocol():
    body = {"protocol_version": PROTOCOL_VERSION + 1, "models": [MODEL]}

    async with fake_ready(body) as url:
        with pytest.raises(SystemExit) as error:
            await check_server(url)

    assert error.value.code not in (0, None)


@pytest.mark.asyncio
async def test_exits_when_the_model_is_missing():
    body = {"protocol_version": PROTOCOL_VERSION, "models": ["tiny.en.pt"]}

    async with fake_ready(body) as url:
        with pytest.raises(SystemExit) as error:
            await check_server(url)

    assert error.value.code not in (0, None)


@pytest.mark.asyncio
async def test_exits_on_an_http_error():
    async with fake_ready({}, status="500 Internal Server Error") as url:
        with pytest.raises(SystemExit) as error:
            await check_server(url)

    assert error.value.code not in (0, None)


@pytest.mark.asyncio
async def test_exits_when_the_server_is_down():
    with pytest.raises(SystemExit) as error:
        await check_server("http://127.0.0.1:1")

    assert error.value.code not in (0, None)
