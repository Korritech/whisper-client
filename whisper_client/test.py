import asyncio;
import json;
import websockets;



async def start_transcription(url="ws://0.0.0.0:8181/ws"):
    result = []
    async with websockets.connect(url) as websocket:
        await asyncio.gather(
            read_audio(websocket, 'test.pcm'),
            read_results(websocket, result)
        )
        print(result)


async def read_audio(websocket, file="test.pcm"):
    await websocket.send('{"type": "start", "model": "small.pt", "language": "fr"}')
    audio = open(file, 'rb')
    data = audio.read()
    await websocket.send(data)
    await asyncio.sleep(0.01)

    await websocket.send('{"type": "flush"}')




async def read_results(websocket, result: list):
    while True:
        try:
            msg = json.loads(await websocket.recv())
            print(msg)
            if not msg["is_partial"]:
                result.append(msg["data"]["text"])
            print(msg["is_partial"], round(msg["time"], 2), msg["data"]["text"])
        except websockets.exceptions.ConnectionClosed:
            print("No transcription available")
            websocket.close()
            return

if __name__ == "__main__":
    asyncio.run(start_transcription())
