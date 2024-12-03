import db, models

from sqlalchemy.future import select
from sqlalchemy import update, delete, exists, insert, func

class _repo:
    model = None
    @classmethod
    async def exists(cls ,where):
        async with db.engine.begin() as conn:
            stmt = select(
                exists().where(where)
            )
            res = await conn.execute(stmt)
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
            return res.scalars().fetchall()
    @classmethod
    async def all(cls):
        async with db.session() as session:
            stmt = select(cls.model)
            res = await session.execute(stmt)
            return res.scalars().fetchall()
    @classmethod
    async def add(cls, obj):
        async with db.session() as session:
            async with session.begin():
                session.add(obj)
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
    @classmethod
    async def count(cls, *where):
        async with db.session() as session:
            async with session.begin():
                stmt = select(func.count()).select_from(cls.model)
                if where:
                    stmt = stmt.where(*where)
                result = await session.execute(stmt)
                return result.scalar()


class user(_repo):
    model = models.User

class participate(_repo):
    model = models.Participate

class admin(_repo):
    model = models.Admin