import os
from datetime import time, datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

from context import Context 
import db
import models
import repo
import services

def participate_allowed():
    maxtime = os.environ.get('TIME')
    if not maxtime:
        raise RuntimeError('set TIME environment')
    maxtime = time(hour=int(maxtime))
    now = datetime.now().time()
    return now < maxtime



class Bot:
    def __init__(self) -> None:
        self.token = os.environ.get('TOKEN')
        if not self.token :
            raise RuntimeError('set TOKEN environment')
        self.channel = os.environ.get('CHANNEL')
        self.app = (
            Application.builder()
            .token(self.token)
            .build()
        )
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle))
        self.app.add_handler(CallbackQueryHandler(self.callback))
    async def handle(self, update: Update, context: CallbackContext):
        tuser = update.effective_user
        bot = context.bot
        if not await self.isJoined(update, context):
            await self.join(update, context)
            return
        if await repo.user.exists(models.User.id==tuser.id):
            user = await repo.user.get(tid=tuser.id)
            if user.step:
                step = user.step
                service = services.UserService(user)
                await service.set_step(None)
                if step=='setp':
                    await self.setp(update,context)
                    return
        await self.main(update, context)

    async def isJoined(self, update:Update, context:CallbackContext):
        tuser = update.effective_user
        bot = context.bot
        chatmember = await bot.get_chat_member(chat_id=self.channel, user_id=tuser.id)
        return chatmember.status in ["member", "administrator", "creator"]

    async def join(self, update:Update, context:CallbackContext):
        text = Context.JOIN_CHANNEL_MESSAGE
        keys = [
            [InlineKeyboardButton(self.channel, url=f'https://t.me/{self.channel[1:]}')],
            [InlineKeyboardButton(Context.JOINED_MESSAGE, callback_data='joined')]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text, 
            reply_markup=InlineKeyboardMarkup(keys))

    async def main(self, update:Update, context: CallbackContext):
        tid = update.effective_user.id
        chat_id = update.effective_chat.id
        if not await repo.user.exists(models.User.id==tid):
            await repo.user.add(models.User(tid=tid, tun=update.effective_user.username))
        user = await repo.user.get(tid=tid)
        service = services.UserService(user)
        ps = await service.get_participates()
        if ps:
            pt = []
            for p in ps:
                v = p.value
                t = p.fortime
                pt += [ Context.PARTICIPATE.format(v=v, t=t) ]
            text = Context.MAIN.format(p='\n'.join(pt))
            keys = [
                [InlineKeyboardButton(Context.CHANGE_VALUE, callback_data='setp')]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keys)
            )
        else:
            text = Context.MAIN_EMPTY
            keys = [
                [InlineKeyboardButton(Context.SET_VALUE, callback_data='setp')]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keys)
            )
    async def participate(self, update:Update, context:CallbackContext):
        chat_id = update.effective_chat.id
        tid = update.effective_user.id
        if not participate_allowed():
            await self.participate_notallowed(update, context)
            return
        if not await self.isJoined(update, context):
            await self.join(update, context)
            return
        await context.bot.send_message(
            chat_id=chat_id,
            text=Context.SEND_VALUE
        )
        user = await repo.user.get(tid=tid)
        service = services.UserService(user)
        await service.set_step('setp')
    
    async def participate_notallowed(self, update:Update, context:CallbackContext):
        chat_id = update.effective_chat.id
        tid = update.effective_user.id
        await context.bot.send_message(
            chat_id=chat_id,
            text=Context.PARTICIPATE_NOTALLOWED,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(Context.OK, callback_data='main')]
                ]
            )
        )

    async def unvalid_result(self, update:Update, context:CallbackContext):
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=Context.UNVALID_RESULT,
        reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(Context.OK, callback_data='setp')
                    ]
                ]
            )
        )


    async def setp(self, update:Update,context:CallbackContext):
        chat_id = update.effective_chat.id
        tid = update.effective_user.id
        value = update.message.text
        if not participate_allowed():
            await self.participate_notallowed(update, context)
            return
        if not value.isdigit():
            await self.unvalid_result(update, context)
            return
        value = int(value)
        if value > 10000000:
            await self.unvalid_result(update, context)
            return
        if not await repo.user.exists(models.User.tid==tid):
            return
        user = await repo.user.get(models.User.tid==tid)
        service = services.UserService(user)
        await service.add_participate(value)
        await context.bot.send_message(
            chat_id=chat_id,
            text=Context.SET_VALUE_DONE,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(Context.OK, callback_data='main')]
                ]
            )
        )


    async def callback(self, update:Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == 'joined':
            if not await self.isJoined(update, context):
                return
            await self.main(update, context)
            return
        if not await self.isJoined(update, context):
            await self.join(update, context)
            return
        if data == 'setp':
            await self.participate(update, context)
            return
        if data == 'main':
            await self.main(update, context)
            return
        await self.main(update, context)

    def start(self):
        self.app.run_polling()