import asyncio
import socket
import sys

import pytest

from whisper_client.server import is_ready, managed_server

FAKE_SERVER = """
import http.server, sys

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):
        pass

http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
"""


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def fake_command(port):
    return [sys.executable, "-c", FAKE_SERVER, str(port)]


@pytest.mark.asyncio
async def test_starts_the_server_then_stops_it():
    port = free_port()
    url = f"http://127.0.0.1:{port}"

    async with managed_server(url, fake_command(port), ".", 10) as process:
        assert process is not None
        assert await is_ready(url)

    assert process.returncode is not None
    assert not await is_ready(url)


@pytest.mark.asyncio
async def test_reuses_a_running_server_and_leaves_it_alive():
    port = free_port()
    url = f"http://127.0.0.1:{port}"

    async with managed_server(url, fake_command(port), ".", 10):
        async with managed_server(url, ["false"], ".", 10) as process:
            assert process is None
        assert await is_ready(url)


@pytest.mark.asyncio
async def test_fails_fast_when_the_server_crashes():
    port = free_port()
    url = f"http://127.0.0.1:{port}"

    with pytest.raises(RuntimeError):
        async with asyncio.timeout(5):
            async with managed_server(url, ["false"], ".", 60):
                pass


@pytest.mark.asyncio
async def test_stops_a_server_that_never_becomes_ready():
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    silent = [sys.executable, "-c", "import time; time.sleep(60)"]

    with pytest.raises(TimeoutError):
        async with managed_server(url, silent, ".", 0.3):
            pass
