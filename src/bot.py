import os
from datetime import time, datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

from context import Context 
import db
import models
import repo
import services

from sqlalchemy import select, and_

def participate_allowed():
    return True
    maxtime = os.environ.get('TIME')
    if not maxtime:
        raise RuntimeError('set TIME environment')
    maxtime = time(hour=int(maxtime))
    now = datetime.now().time()
    return now < maxtime

def start_today():
    td = datetime.now().date()
    return datetime(
        year=td.year,
        day=td.day,
        month=td.month,
    )

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
            [InlineKeyboardButton(self.channel, url=f'https://t.me/{self.channel[1:]}')],
            [InlineKeyboardButton(Context.JOINED_MESSAGE.encode('utf-8'), callback_data='joined')]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text.encode('utf-8'), 
            reply_markup=InlineKeyboardMarkup(keys))
    async def ensure_user(self, update:Update, context: CallbackContext):
        tid = update.effective_user.id
        if not await repo.user.exists(models.User.tid==tid):
            await repo.user.add(models.User(tid=tid, tun=update.effective_user.username))

    async def main(self, update:Update, context: CallbackContext):
        tid = update.effective_user.id
        chat_id = update.effective_chat.id
        user = await repo.user.get(models.User.tid==tid)
        service = services.UserService(user)
        ps = await repo.participate.filter(
            and_(
                models.Participate.user==user,
                models.Participate.settime > start_today()
            )
        )
        if ps:
            pt = []
            for p in ps:
                v = p.value
                t:datetime = p.fortime.replace(microsecond=0)
                pt += [ Context.PARTICIPATE.format(v=v, t=t) ]
            text = Context.MAIN.format(p='\n'.join(pt))
            keys = [
                [InlineKeyboardButton(Context.CHANGE_VALUE.encode('utf-8'), callback_data='setp')]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text=text.encode('utf-8'),
                reply_markup=InlineKeyboardMarkup(keys)
            )
        else:
            text = Context.MAIN_EMPTY
            keys = [
                [InlineKeyboardButton(Context.SET_VALUE.encode('utf-8'), callback_data='setp')]
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text=text.encode('utf-8'),
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
            text=Context.SEND_VALUE.encode('utf-8')
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
                    [InlineKeyboardButton(Context.OK.encode('utf-8'), callback_data='main')]
                ]
            )
        )

    async def unvalid_result(self, update:Update, context:CallbackContext):
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=Context.UNVALID_RESULT.encode('utf-8'),
        reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(Context.OK.encode('utf-8'), callback_data='setp')
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
        async with db.session() as session:
            res = await session.execute(
                select(models.Participate).where(
                    and_(
                        models.Participate.user==user,
                        models.Participate.fortime > start_today()
                    )
                    ).order_by(models.Participate.fortime.desc()).limit(3)
            )
            ps = res.scalars().fetchall()
        if len(ps) > 2:
            remain = (start_today() + timedelta(days=1)) - datetime.now()
            remain = timedelta(
                seconds=int(remain.total_seconds())
            ).__str__()
            await context.bot.send_message(
                chat_id=chat_id,
                text=Context.MAX_PARTICIPATE.format(t=remain).encode('utf-8'),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(Context.OK.encode('utf-8'), callback_data='main')]
                    ]
                )
            )
            return

        if ps and ps[0].fortime > datetime.now():
            remain:timedelta = ps[0].fortime - datetime.now()
            remain = timedelta(
                seconds=int(remain.total_seconds())
            ).__str__()
            await context.bot.send_message(
                chat_id=chat_id,
                text=Context.TOOMANY_PARTICIPATE.format(t=remain),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(Context.OK.encode('utf-8'), callback_data='main')]
                    ]
                )
            )
            return
        await service.add_participate(value)
        await context.bot.send_message(
            chat_id=chat_id,
            text=Context.SET_VALUE_DONE.format(p=value).encode('utf-8'),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(Context.OK.encode('utf-8'), callback_data='main')]
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
        await self.ensure_user(update, context)
        if data == 'setp':
            await self.participate(update, context)
            return
        if data == 'main':
            await self.main(update, context)
            return
        await self.main(update, context)

    def start(self):
        self.app.run_polling()