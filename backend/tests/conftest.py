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

TEST_DATABASE_URL = "sqlite+aiosqlite:///./backend/tests/test.db"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestingSessionLocal = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Cria e destrói o esquema do banco isolado para cada teste."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Cria um cliente HTTP de teste com a dependência de banco substituída pela sessão de teste."""

    # Substitui a dependência de banco pela sessão de teste
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def token_gerente(client: AsyncClient, db_session: AsyncSession) -> str:
    """Persiste um Gerente de teste no banco e retorna seu token JWT."""
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
    """Persiste um Recepcionista de teste no banco e retorna seu token JWT."""
    repo = UsuarioRepository(db_session)
    recep = Recepcionista(
        nome="Recep Teste",
        email="recep@teste.com",
        senha_hash=Usuario.gerar_hash("recep123")
    )
    await repo.salvar(recep)
    resp = await client.post("/auth/login", data={"username": "recep@teste.com", "password": "recep123"})
    return resp.json()["access_token"]