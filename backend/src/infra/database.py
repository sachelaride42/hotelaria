import os
from dotenv import load_dotenv
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base


# Em produção, isso viria de variáveis de ambiente (.env)
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8")

# postgresql+asyncpg é o driver assíncrono super rápido para Postgres
DATABASE_URL = os.getenv(
    "DATABASE_URL_ASYNC",
)
if not DATABASE_URL:
    raise ValueError("A variável DATABASE_URL_ASYNC não foi encontrada no .env")


# 1. O Motor (Engine)
# Ele gerencia o pool de conexões com o banco de dados.
engine = create_async_engine(
    DATABASE_URL,
    echo=True,          # Imprime o SQL gerado no console (ótimo para debug no TCC)
    pool_size=5,        # Mantém 5 conexões abertas prontas para uso
    max_overflow=10,    # Permite criar até 10 conexões extras em picos de tráfego
    pool_pre_ping=True  # Testa se a conexão está viva antes de usar (evita erros de timeout)
)

# 2. A Fábrica de Sessões (SessionMaker)
# Cria sessões assíncronas isoladas para cada requisição da nossa API.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Evita que o SQLAlchemy apague os dados da memória após o commit
    autocommit=False,
    autoflush=False
)

# 3. Base Declarativa
# Todos os modelos ORM (como o QuartoORM) herdam dessa classe.
Base = declarative_base()

# 4. Injeção de Dependência (Generator) para o FastAPI
# Essa é a função que chamamos nas rotas com `Depends(get_db_session)`
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Cria uma nova sessão de banco de dados para a requisição.
    O bloco `async with` garante que a conexão será fechada (devolvida ao pool)
    assim que a requisição terminar, mesmo que ocorra um erro na API.
    """
    async with AsyncSessionLocal() as session:
        yield session