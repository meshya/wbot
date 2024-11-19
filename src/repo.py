import db, models

from sqlalchemy.future import select
from sqlalchemy import update, delete, exists

class _repo:
    model = None
    @classmethod
    async def exists(cls ,where):
        async with db.session() as session:
            stmt = select(
                exists().where(where)
            )
            res = await session.execute(stmt)
            return res.scalar()
    @classmethod
    async def get(cls, where):
        async with db.session() as session:
            res = await session.execute(
                select(cls.model).where(where)
            )
            obj = res.scalar_one_or_none()
            return obj
    @classmethod
    async def filter(cls, where):
        async with db.session() as session:
            stmt = select(cls.model).where(where)
            res = await session.execute(stmt)
            return list(
                res.scalar()
            )
    @classmethod
    async def add(cls, obj):
        async with db.session() as session:
            async with session.begin():
                await session.add(obj)
    @classmethod
    def update(cls, **upd):
        class callback:
            async def where(self, where):
                async with db.engine.begin() as conn:
                    stmt = update(cls.model).where(where).values(**upd)
                    await conn.execute(stmt)
        return callback()
    @classmethod
    async def delete(cls, where):
        async with db.engine.begin() as conn:
            stmt = delete(cls.model).where(where)
            await conn.execute(stmt)


class user(_repo):
    model = models.User

class participate(_repo):
    model = models.Participate