import asyncio

import json
import httpx
import websockets
from contextlib import aclosing
import logging
from whisper_client.server import fetch_ready, check_server
from whisper_client.config import LANGUAGE,MODEL,PROMPTS, WS_URL


log = logging.getLogger(__name__)

async def dictate(chunks, url=WS_URL, model=MODEL, language=LANGUAGE, prompt=PROMPTS[LANGUAGE]):
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps({"type": "start", "model": model, "language": language, "prompt": prompt}))

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
