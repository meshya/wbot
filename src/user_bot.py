import os
from datetime import time, datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import  CallbackContext

from context import Context 
import db
import models
import repo
import services

from sqlalchemy import select, and_

from bot import Bot

def participate_allowed():
    maxtime = os.environ.get('END_TIME')
    mintime = os.environ.get('START_TIME')
    if not maxtime or not mintime:
        raise RuntimeError('set START_TIME and END_TIME environment')
    maxtime = time(hour=int(maxtime))
    mintime = time(hour=int(mintime))
    now = datetime.now().time()
    return now < maxtime and now > mintime

def start_today():
    td = datetime.now().date()
    return datetime(
        year=td.year,
        day=td.day,
        month=td.month,
    )

class UserBot(Bot):
    def __init__(self, token) -> None:
        super().__init__(token)
        self.channel = os.environ.get('CHANNEL')

    async def handle(self, update: Update, context: CallbackContext):
        tuser = update.effective_user
        bot = context.bot
        if not await self.isJoined(update, context):
            await self.join(update, context)
            return
        await self.ensure_user(update, context)
        user = await repo.user.get(models.User.tid==tuser.id)
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
            [InlineKeyboardButton(Context.CHANNEL_JOIN_BUTTON, url=f'https://t.me/{self.channel[1:]}')],
            [InlineKeyboardButton(Context.JOINED_MESSAGE, callback_data='joined')]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text, 
            reply_markup=InlineKeyboardMarkup(keys))

    async def joined(self, update:Update, context:CallbackContext):
        text = Context.JOIN_SUCCESSFUL
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text
        )

    async def not_joined(self, update:Update, context:CallbackContext):
        text = Context.JOIN_FAILED
        keys = [
            [InlineKeyboardButton(Context.CHANNEL_JOIN_BUTTON, url=f'https://t.me/{self.channel[1:]}')],
            [InlineKeyboardButton(Context.JOINED_MESSAGE, callback_data='joined')]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text, 
            reply_markup=InlineKeyboardMarkup(keys))

    async def main(self, update:Update, context: CallbackContext):
        tid = update.effective_user.id
        chat_id = update.effective_chat.id
        user = await repo.user.get(models.User.tid==tid)
        service = services.UserService(user)
        if await service.exists_participate():
            p = await service.get_participate()
            t = p.settime.date()
            p = Context.PARTICIPATE.format(
                t=str(t),
                v=p.value
            )
            text = Context.MAIN.format(p=p)
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
        where = models.User.tid==tid
        user = await repo.user.get(where)
        if not user:
            await self.main(update, context)
            
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
                        InlineKeyboardButton(Context.RETRY, callback_data='setp'),
                        InlineKeyboardButton(Context.RETURN, callback_data='main')
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
        await service.set_participate(value)
        await context.bot.send_message(
            chat_id=chat_id,
            text=Context.SET_VALUE_DONE.format(p=value),
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
                await self.not_joined(update, context)
            else:
                await self.joined(update, context)
                await self.main(update, context)
            return
        if not await self.isJoined(update, context):
            await self.join(update, context)
            return
        await self.ensure_user(update, context)
        if data == 'setp':
            await self.participate(update, context)
            return
        if data == 'main':
            await self.main(update, context)
            return
        await self.main(update, context)
