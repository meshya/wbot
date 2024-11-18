from datetime import datetime, time, timedelta, date

import models
import repo

class UserService:
    def __init__(self, user:models.User) -> None:
        self.user = user
    async def get_participate(self):
        ptime:datetime = self.user.ptime
        if ptime and ptime.date() != date.today():
            return None
        return self.user.p
    async def set_step(self, step):
        await repo.user.update(step=step).where(models.User.id==self.user.id)
    async def set_participate(self, value):
        await repo.user.update(p=value, ptime=datetime.now()).where(models.User.id==self.user.id)