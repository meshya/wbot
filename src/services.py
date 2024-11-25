from datetime import datetime, time, timedelta, date
from sqlalchemy import Select, and_

import models
import repo
import db

def start_today():
    td = datetime.now().date()
    return datetime(
        year=td.year,
        day=td.day,
        month=td.month,
    )


class UserService:
    def __init__(self, user:models.User) -> None:
        self.user = user
    async def get_participate(self):
        where = and_(
                models.Participate.user==self.user,
                models.Participate.settime > start_today()
            )
        return await repo.participate.get(where)
    async def set_step(self, step):
        await repo.user.update(step=step).where(models.User.id==self.user.id)
    async def set_participate(self, value):
        settime = datetime.now()
        fortime = start_today() + timedelta(days=1)
        where = and_(
                models.Participate.user==self.user,
                models.Participate.settime > start_today()
            )
        if await repo.participate.exists(where):
            await repo.participate.update(value=value).where(where)
        else:
            await repo.participate.add(
                models.Participate(
                    user=self.user,
                    value=value,
                    settime=settime,
                    fortime=fortime
                )
            )
    async def exists_participate(self):
        where = and_(
                models.Participate.user==self.user,
                models.Participate.settime > start_today()
            )
        return await repo.participate.exists(where)


class ParticipateService:
    async def get_participates(self, value, limit):
        async with db.session() as session:
            today = datetime.now().replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )
            stmt = Select(models.Participate).where(
                and_(
                    models.Participate.settime < today + timedelta(days=1),
                    models.Participate.settime > today
                )
            ).order_by(
                (models.Participate.value - value).abs().asc()
            ).limit(limit)
            res = await session.execute(stmt)
            return res.scalars().fetchall()