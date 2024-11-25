from telegram import Bot

import repo

from multiprocessing import Process
import asyncio

def broadcast(token, text):
    bot = Bot(token)
    class Do:
        @classmethod
        def start(cls):
            def _p():
                asyncio.run(cls.do())
            Process(target=_p).start()
        @classmethod
        async def do(cls):
            users = await repo.user.all()
            for user in users:
                await bot.send_message(
                    chat_id=user.tid,
                    text=text
                )
    return Do