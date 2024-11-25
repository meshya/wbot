from bot import Bot
from context import Context
from broadcast import broadcast
import repo
import models
import services

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

import os
from multiprocessing import Process

class AdminBot(Bot):
    async def Allowed(self, update:Update, context:CallbackContext):
        tun = update.effective_chat.username
        if tun == 'meshyah':
            return True
        return await repo.admin.exists(models.Admin.tun==tun)
    async def handle(self, update:Update, context:CallbackContext):
        if not await self.Allowed(update, context):
            return
        tid = update.effective_user.id
        await self.ensure_user(update, context)
        where = models.User.tid==tid
        user = await repo.user.get(where)
        step = user.step
        if step:
            await repo.user.update(step=None).where(where)
            if step == 'filter':
                await self.filter(update, context)
                return
        await self.main(update, context)
    
    async def main(self, update:Update, context:CallbackContext):
        cid = update.effective_chat.id
        await context.bot.send_message(
            chat_id = cid,
            text = Context.ADMIN_MAIN,
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            Context.BROADCAST_BUTTON,
                            callback_data='broadcast'
                        ),
                        InlineKeyboardButton(
                            Context.FILTER_USER_BUTTON,
                            callback_data='filter'
                        )
                    ]
                ]
            )
        )

    async def filter_intro(self, update:Update, context:CallbackContext):
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = Context.FILTER_USER
        )
        await repo.user.update(step='filter').where(
            models.User.tid == update.effective_user.id
        )
    async def filter(self, update:Update, context:CallbackContext):
        value = update.message.text
        if not value.isdigit():
            await self.main(update, context)
            return
        value = int(value)
        participates = services.ParticipateService().get_participates(value, 10)
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = Context.FILTER_RESULT_ALL.format(
                r='\n'.join(
                    map(
                        lambda p: Context.FILTER_RESULT.format(
                            n=p.user.tn,
                            un=p.user.tun,
                            v=p.value,
                            t=p.settime.replace(microsecond=0)
                        ), participates
                    )
                )
            )
        )

    async def broadcast(self, update:Update, context:Context):
        message = update.message.text
        token = os.environ.get('TOKEN')
        broadcast(token, message).start()

    async def callback(self, update:Update, context:CallbackContext):
        if not await self.Allowed(update, context):
            return
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == 'filter':
            await self.filter_intro(update, context)
        elif data == 'broadcast':
            await self.broadcast(update, context)
        else:
            await self.main(update, context)
