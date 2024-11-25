from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from telegram import Update

import models
import repo

class Bot:
    def __init__(self, token) -> None:
        self.token = token
        if not self.token :
            raise RuntimeError('set TOKEN environment')
        self.app = (
            Application.builder()
            .token(self.token)
            .build()
        )
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle))
        self.app.add_handler(CallbackQueryHandler(self.callback))
        print(f'bot created {type(self).__name__}')
    async def ensure_user(self, update:Update, context: CallbackContext):
        tid = update.effective_user.id
        name = (update.effective_user.first_name or '').strip() + ' ' + (update.effective_user.last_name or '').strip()
        if not await repo.user.exists(models.User.tid==tid):
            await repo.user.add(models.User(tid=tid, tun=update.effective_user.username, tn=f'{name}'))
    async def callback(self, up, con):
        raise RuntimeError()
    async def handle(self, up, con):
        raise RuntimeError()
    def start(self):
        print(f'bot started {type(self).__name__}')
        self.app.run_polling()