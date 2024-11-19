from datetime import datetime, time, timedelta, date

import models
import repo

class UserService:
    def __init__(self, user:models.User) -> None:
        self.user = user
    async def get_participates(self):
        return await repo.participate.filter(models.Participate.user==self.user)
    async def set_step(self, step):
        await repo.user.update(step=step).where(models.User.id==self.user.id)
    async def add_participate(self, value):
        settime = datetime.now()
        fortime = settime + timedelta(hours=1)
        obj = models.User(value=value, settime=settime, fortime=fortime)
        await repo.participate.add(obj)