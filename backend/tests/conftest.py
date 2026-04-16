import pytest
import pytest_asyncio
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.src.infra.database import Base
from httpx import AsyncClient, ASGITransport
from backend.src.main import app  # Importa a aplicação FastAPI
from backend.src.infra.database import get_db_session
from backend.src.domain.models.usuario import Gerente, Recepcionista, Usuario
from backend.src.infra.repositories.usuario_repository import UsuarioRepository

# Usamos SQLite em memória para os testes rodarem de forma ultra-rápida e isolada
TEST_DATABASE_URL = "sqlite+aiosqlite:///./backend/tests/test.db"


engine_test = create_async_engine(
    TEST_DATABASE_URL,  # continua "sqlite+aiosqlite:///./backend/tests/test.db"
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # ← única mudança
    echo=False
)

TestingSessionLocal = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Cria um banco novo e limpo para cada teste executado."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """
    Cria um cliente HTTP simulado para testar as rotas.
    Ele substitui o banco de dados principal pelo banco de testes.
    """

    # Override da injeção de dependência!
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    # Cria o cliente HTTP assíncrono conectado ao app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # Limpa o override após o teste
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def token_gerente(client: AsyncClient, db_session: AsyncSession) -> str:
    """Cria um Gerente diretamente no banco (bypassando a API) e retorna o JWT de acesso."""
    repo = UsuarioRepository(db_session)
    gerente = Gerente(
        nome="Gerente Teste",
        email="gerente@teste.com",
        senha_hash=Usuario.gerar_hash("gerente123")
    )
    await repo.salvar(gerente)
    resp = await client.post("/auth/login", data={"username": "gerente@teste.com", "password": "gerente123"})
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def token_recepcionista(client: AsyncClient, db_session: AsyncSession) -> str:
    """Cria um Recepcionista diretamente no banco (bypassando a API) e retorna o JWT de acesso."""
    repo = UsuarioRepository(db_session)
    recep = Recepcionista(
        nome="Recep Teste",
        email="recep@teste.com",
        senha_hash=Usuario.gerar_hash("recep123")
    )
    await repo.salvar(recep)
    resp = await client.post("/auth/login", data={"username": "recep@teste.com", "password": "recep123"})
    return resp.json()["access_token"]