import asyncio

import json
import websockets
from contextlib import aclosing


WS_URL="ws://127.0.0.1:8181/ws"


async def dictate(chunks, url=WS_URL):
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps({"type": "start", "model": "small.pt", "language": "fr"}))

        async with asyncio.TaskGroup() as group:
            group.create_task(send_audio(websocket, chunks))
            dictation = group.create_task(read_results(websocket))

    return " ".join(t.strip() for t in dictation.result())

async def read_results(websocket: websockets.ClientConnection):
    results = []
    async for raw in websocket:
        res = json.loads(raw)
        if res.get("type") == "error":
            print("Error", res["message"])
            continue
        if not res["is_partial"]:
            results.append(res["data"]["text"])
        # else :
            # print("[Partial] ", res["data"]["text"])

    return results


async def send_audio(websocket: websockets.ClientConnection, chunks):
    async with aclosing(chunks) as source:
        async for chunk in source:
            await websocket.send(chunk)
    await websocket.send(json.dumps({"type":"stop"}))
