import asyncio

import json
import httpx
import websockets
from contextlib import aclosing
import logging

HTTP_URL="http://127.0.0.1:8181"
PROTOCOL_VERSION = 1
WS_URL="ws://127.0.0.1:8181/ws"
PROMPT = "Je développe avec Claude Code en Python, avec asyncio et des WebSocket."
MODEL = "small.pt"

log = logging.getLogger(__name__)

async def check_server(base_url=HTTP_URL):

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/ready")
    except httpx.TransportError:
        log.warning("WhisperFlow server not ready")
        return
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise SystemExit("WhisperFlow server not available. Status %d", e.response.status_code)

    info = response.json()
    if info["protocol_version"] != PROTOCOL_VERSION:
        raise SystemExit(f"[Error] Invalid protocol version. Received {info['protocol_version']}, expected {PROTOCOL_VERSION}")
    if MODEL not in info["models"]:
        raise SystemExit(f"[Error] Invalid model. Received {info['models']}, expected {MODEL}")


async def dictate(chunks, url=WS_URL):
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps({"type": "start", "model": MODEL, "language": "fr", "prompt": PROMPT}))

        async with asyncio.TaskGroup() as group:
            group.create_task(send_audio(websocket, chunks))
            dictation = group.create_task(read_results(websocket))

    return " ".join(t.strip() for t in dictation.result())

async def read_results(websocket: websockets.ClientConnection):
    results = []
    async for raw in websocket:
        res = json.loads(raw)
        if res.get("type") == "error":
            log.error({res['message']})
            continue
        if not res["is_partial"]:
            results.append(res["data"]["text"])
        else :
            log.debug("[Partial] %s", res["data"]["text"])

    return results


async def send_audio(websocket: websockets.ClientConnection, chunks):
    async with aclosing(chunks) as source:
        async for chunk in source:
            await websocket.send(chunk)
    await websocket.send(json.dumps({"type":"stop"}))
