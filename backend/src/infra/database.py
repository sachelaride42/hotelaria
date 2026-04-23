import os
from dotenv import load_dotenv
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base


env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8")

DATABASE_URL = os.getenv(
    "DATABASE_URL_ASYNC",
)
if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL_ASYNC não foi encontrada no .env")


engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Abre uma sessão de banco de dados e a fecha ao término da requisição."""
    async with AsyncSessionLocal() as session:
        yield session