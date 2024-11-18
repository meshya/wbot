import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DB_URL = os.environ.get('DB_URL')
if not DB_URL:
    raise RuntimeError('set DB_URL environment')

engine = create_async_engine(DB_URL)
session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
