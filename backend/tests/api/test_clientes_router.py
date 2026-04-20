import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_criar_cliente_sucesso(client: AsyncClient, token_recepcionista: str):
    """Testa o endpoint de criação de cliente com sucesso (HTTP 201)"""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {
        "nome": "João da Silva",
        "telefone": "11999999999",
        "cpf": "12345678901"
    }

    response = await client.post("/clientes/", json=payload, headers=headers)

    assert response.status_code == 201
    dados = response.json()
    assert dados["nome"] == "João da Silva"
    assert "id" in dados


@pytest.mark.asyncio
async def test_api_criar_cliente_sem_nome_retorna_400(client: AsyncClient, token_recepcionista: str):
    """O schema/domínio deve barrar a falta de nome (HTTP 400)"""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {"nome": "", "telefone": "11999999999"}

    response = await client.post("/clientes/", json=payload, headers=headers)

    assert response.status_code == 400
    assert "O campo 'Nome' é obrigatório" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_criar_cliente_cpf_duplicado_retorna_409(client: AsyncClient, token_recepcionista: str):
    """A Exceção de concorrência do banco vira HTTP 409 Conflict"""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {"nome": "Maria", "telefone": "111", "cpf": "11122233344"}

    # Primeira inserção
    await client.post("/clientes/", json=payload, headers=headers)

    # Segunda inserção com o mesmo CPF
    response = await client.post("/clientes/", json=payload, headers=headers)

    assert response.status_code == 409
    assert "CPF já cadastrado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_criar_cliente_sem_token_retorna_401(client: AsyncClient):
    """Rota de clientes exige autenticação."""
    response = await client.post("/clientes/", json={"nome": "X", "telefone": "1"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_cliente_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente deleta um cliente com sucesso."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    resp_criar = await client.post("/clientes/", json={"nome": "Para Deletar", "telefone": "999", "cpf": "11122233344"}, headers=g_headers)
    cliente_id = resp_criar.json()["id"]

    response = await client.delete(f"/clientes/{cliente_id}", headers=g_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_api_deletar_cliente_nao_encontrado_retorna_404(client: AsyncClient, token_gerente: str):
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.delete("/clientes/9999", headers=g_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_deletar_cliente_sem_token_retorna_401(client: AsyncClient):
    response = await client.delete("/clientes/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_cliente_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str, token_gerente: str):
    """Recepcionista não pode deletar clientes."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    resp_criar = await client.post("/clientes/", json={"nome": "Alvo", "telefone": "111", "cpf": "99988877766"}, headers=r_headers)
    cliente_id = resp_criar.json()["id"]

    response = await client.delete(f"/clientes/{cliente_id}", headers=r_headers)
    assert response.status_code == 403
