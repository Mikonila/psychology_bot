# db_start.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("DB_URL", "postgresql+asyncpg://postgres:postgres@db:5432/ps_bot")

engine = create_async_engine(DB_URL, echo=False, future=True, pool_pre_ping=True)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
