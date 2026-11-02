
import asyncio

START = "/System/Library/Sounds/Tink.aiff"
STOP = "/System/Library/Sounds/Pop.aiff"
ERROR = "/System/Library/Sounds/Basso.aiff"


async def play(sound):
    await asyncio.create_subprocess_exec("afplay", sound)

async def silent(sound):
    pass
