
import asyncio
import os
import json

from contextlib import asynccontextmanager
from pathlib import Path
import httpx
import logging

log = logging.getLogger(__name__)

from whisper_client.config import HTTP_URL, MODEL, PROTOCOL_VERSION, SERVER_DIR, START_TIMEOUT, STOP_TIMEOUT

SERVER_COMMAND = [
    str(SERVER_DIR / ".venv/bin/uvicorn"),
    "whisperflow.fast_server:app",
    "--host", "127.0.0.1",
    "--port", "8181",
]

async def fetch_ready(base_url=HTTP_URL):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/ready", timeout=1)
    response.raise_for_status()
    return response.json()

async def get_models(base_url=HTTP_URL):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/ready", timeout=1)

    if(response.is_success):
        resp_json = json.loads(response.text)
        if resp_json["models"]:
            return  resp_json["models"]

    return []



async def is_ready(base_url=HTTP_URL):
    try:
        await fetch_ready(base_url)
    except httpx.HTTPError:
        return False
    return True

async def check_server(base_url=HTTP_URL):
    try:
        info = await fetch_ready(base_url)
    except httpx.HTTPError as e:
        raise SystemExit(f"WhisperFlow server not available: {e!r}")

    if info["protocol_version"] != PROTOCOL_VERSION:
        raise SystemExit(f"[Error] Invalid protocol version. Received {info['protocol_version']}, expected {PROTOCOL_VERSION}")
    if MODEL not in info["models"]:
        raise SystemExit(f"[Error] Invalid model. Received {info['models']}, expected {MODEL}")


async def wait_until_ready(process, base_url, timeout):
    async with asyncio.timeout(timeout):
        while not await is_ready(base_url):
            if process.returncode is not None:
                raise RuntimeError("WhisperFlow server exited during startup")
            await asyncio.sleep(0.2)


async def stop_server(process):
    if process.returncode is not None:
        return

    log.info("Stop server")
    process.terminate()
    try:
        async with asyncio.timeout(STOP_TIMEOUT):
            await process.wait()
    except TimeoutError:
        log.warning("Server did not stop, killing it")
        process.kill()
        await process.wait()


@asynccontextmanager
async def managed_server(base_url=HTTP_URL, command=SERVER_COMMAND,
                         cwd=SERVER_DIR, timeout=START_TIMEOUT):
    if await is_ready(base_url):
        yield None    # un serveur tourne déjà : il ne nous appartient pas
        return

    process = await asyncio.create_subprocess_exec(
        *command, cwd=cwd, env={**os.environ, "WF_MODEL": MODEL}
    )
    try:
        await wait_until_ready(process, base_url, timeout)
        yield process
    finally:
        await stop_server(process)
