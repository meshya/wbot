from context import Context
from broadcast import broadcast

import asyncio
import os

token = os.environ.get('TOKEN')
if not token:
    raise RuntimeError('set TOKEN environ')

async def main():
    await broadcast(
        token,
        Context.END_GAME
    ).do()
