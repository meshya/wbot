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
        tun = update.effective_user.username
        if tun.lower() in ['meshyah', 'ha493']:
            return True
        return await repo.admin.exists(models.Admin.tun==tun.lower())
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
            if step == 'broadcast':
                await self.broadcast(update, context)
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
                        )
                    ],[
                        InlineKeyboardButton(
                            Context.FILTER_USER_BUTTON,
                            callback_data='filter'
                        )
                    ],[
                        InlineKeyboardButton(
                            Context.REPORT_BUTTON,
                            callback_data='report'
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
        participates = await services.ParticipateService().get_participates(value, 10)
        results = []
        for p in participates:
            user = await repo.user.get(models.User.id==p.user_id)
            c = Context.FILTER_RESULT.format(
                n=user.tn,
                un=user.tun,
                v=p.value,
                t=p.settime.replace(microsecond=0)
            )
            results.append(c)
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = Context.FILTER_RESULT_ALL.format(
                r='\n'.join(
                    results
                )
            )
        )

    async def broadcast(self, update:Update, context:Context):
        message = update.message.text
        token = os.environ.get('TOKEN')
        await broadcast(token, message).do()

    async def broadcast_intro(self, update:Update, context:CallbackContext):
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = Context.BROADCAST
        )
        await repo.user.update(step='broadcast').where(
            models.User.tid == update.effective_user.id
        )

    async def report(self, update:Update, context:CallbackContext):
        all_users = await repo.user.count()
        today_participates = await services.ParticipateService().count_participates() 
        avg_participates = await services.ParticipateService().avg_participates()
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = Context.REPORT.format(
                u = all_users,
                p = today_participates,
                v = avg_participates
            )
        )

    async def callback(self, update:Update, context:CallbackContext):
        if not await self.Allowed(update, context):
            return
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == 'filter':
            await self.filter_intro(update, context)
        elif data == 'broadcast':
            await self.broadcast_intro(update, context)
        elif data == 'report':
            await self.report(update, context)
        else:
            await self.main(update, context)
