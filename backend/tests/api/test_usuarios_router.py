import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_criar_usuario_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente pode criar novos usuários."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {
        "nome": "Carlos Gerente",
        "email": "carlos@hotel.com",
        "senha": "senha_forte_123",
        "tipo": "GERENTE"
    }

    response = await client.post("/usuarios/", json=payload, headers=headers)

    assert response.status_code == 201
    dados = response.json()
    assert dados["nome"] == "Carlos Gerente"
    assert dados["email"] == "carlos@hotel.com"
    assert "senha" not in dados  # REGRA DE OURO: A senha nunca deve voltar na resposta!


@pytest.mark.asyncio
async def test_api_impedir_email_duplicado(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {
        "nome": "Ana Recepcão",
        "email": "ana@hotel.com",
        "senha": "123456",
        "tipo": "RECEPCIONISTA"
    }

    # 1. Cria a primeira vez (Sucesso)
    primeiro = await client.post("/usuarios/", json=payload, headers=headers)
    assert primeiro.status_code == 201

    # 2. Tenta criar de novo (Falha)
    response = await client.post("/usuarios/", json=payload, headers=headers)
    assert response.status_code == 409
    assert "Já existe um utilizador" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_criar_usuario_sem_token_retorna_401(client: AsyncClient):
    """Endpoint de criação de usuário exige autenticação."""
    payload = {"nome": "Ninguém", "email": "x@hotel.com", "senha": "123456", "tipo": "RECEPCIONISTA"}
    response = await client.post("/usuarios/", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_criar_usuario_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Apenas Gerentes podem criar usuários — Recepcionistas recebem 403."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {"nome": "Novo", "email": "novo@hotel.com", "senha": "123456", "tipo": "RECEPCIONISTA"}
    response = await client.post("/usuarios/", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Acesso negado" in response.json()["detail"]
