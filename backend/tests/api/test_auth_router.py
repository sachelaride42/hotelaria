import pytest
from httpx import AsyncClient
from fastapi import APIRouter, Depends
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.src.api.dependencies.seguranca import exigir_gerente
from backend.src.main import app # Importa a app principal do FastAPI
from backend.src.domain.models.usuario import Gerente, Recepcionista, Usuario
from backend.src.infra.repositories.usuario_repository import UsuarioRepository

# É injetada uma rota temporária na app apenas para testar a tranca do Gerente
rota_teste = APIRouter()
@rota_teste.get("/rota-secreta-gerente", dependencies=[Depends(exigir_gerente)])
async def rota_secreta():
    return {"mensagem": "Acesso concedido ao cofre!"}
app.include_router(rota_teste)


@pytest_asyncio.fixture
async def setup_usuarios_teste(client: AsyncClient, db_session: AsyncSession):
    """Cria dois utilizadores diretamente no banco para os testes de login."""
    repo = UsuarioRepository(db_session)
    await repo.salvar(Gerente(
        nome="Chefe",
        email="chefe@hotel.com",
        senha_hash=Usuario.gerar_hash("123456")
    ))
    await repo.salvar(Recepcionista(
        nome="Atendente",
        email="atendimento@hotel.com",
        senha_hash=Usuario.gerar_hash("abcdef")
    ))


@pytest.mark.asyncio
async def test_api_login_sucesso_retorna_token(client: AsyncClient, setup_usuarios_teste):
    # O OAuth2 exige envio como Form Data (data) e não JSON.
    form_data = {"username": "chefe@hotel.com", "password": "123456"}
    
    response = await client.post("/auth/login", data=form_data)
    
    assert response.status_code == 200
    dados = response.json()
    assert "access_token" in dados
    assert dados["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_api_login_senha_incorreta(client: AsyncClient, setup_usuarios_teste):
    form_data = {"username": "chefe@hotel.com", "password": "senha_errada"}
    response = await client.post("/auth/login", data=form_data)
    
    assert response.status_code == 401
    assert "E-mail ou senha incorretos" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rbac_recepcionista_nao_pode_acessar_rota_de_gerente(client: AsyncClient, setup_usuarios_teste):
    """Testa o Role-Based Access Control (RBAC)."""
    
    # 1. Faz login como RECEPCIONISTA para roubar o token
    resp_login = await client.post("/auth/login", data={"username": "atendimento@hotel.com", "password": "abcdef"})
    token_recepcionista = resp_login.json()["access_token"]
    
    # 2. Tenta bater na porta da rota protegida usando o token
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.get("/rota-secreta-gerente", headers=headers)
    
    # 3. O FastAPI deve barrar com 403 Forbidden!
    assert response.status_code == 403
    assert "Acesso negado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rbac_gerente_acessa_rota_com_sucesso(client: AsyncClient, setup_usuarios_teste):
    """Garante que o Gerente passa pela tranca normalmente."""
    
    # 1. Faz login como GERENTE
    resp_login = await client.post("/auth/login", data={"username": "chefe@hotel.com", "password": "123456"})
    token_gerente = resp_login.json()["access_token"]
    
    # 2. Acessa a rota protegida
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.get("/rota-secreta-gerente", headers=headers)
    
    # 3. Sucesso!
    assert response.status_code == 200
    assert response.json()["mensagem"] == "Acesso concedido ao cofre!"