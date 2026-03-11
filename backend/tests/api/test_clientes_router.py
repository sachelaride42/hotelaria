import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_criar_cliente_sucesso(client: AsyncClient):
    """Testa o endpoint de criação de cliente com sucesso (HTTP 201)"""
    payload = {
        "nome": "João da Silva",
        "telefone": "11999999999",
        "cpf": "12345678901"
    }

    response = await client.post("/clientes/", json=payload)

    assert response.status_code == 201
    dados = response.json()
    assert dados["nome"] == "João da Silva"
    assert "id" in dados


@pytest.mark.asyncio
async def test_api_criar_cliente_sem_nome_retorna_400(client: AsyncClient):
    """O schema/domínio deve barrar a falta de nome (HTTP 400)"""
    payload = {"nome": "", "telefone": "11999999999"}

    response = await client.post("/clientes/", json=payload)

    assert response.status_code == 400
    assert "O campo 'Nome' é obrigatório" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_criar_cliente_cpf_duplicado_retorna_409(client: AsyncClient):
    """A Exceção de concorrência do banco vira HTTP 409 Conflict"""
    payload = {"nome": "Maria", "telefone": "111", "cpf": "11122233344"}

    # Primeira inserção
    await client.post("/clientes/", json=payload)

    # Segunda inserção com o mesmo CPF
    response = await client.post("/clientes/", json=payload)

    assert response.status_code == 409
    assert "CPF já cadastrado" in response.json()["detail"]