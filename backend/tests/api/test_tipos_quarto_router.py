import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_criar_tipo_quarto_sucesso(client: AsyncClient, token_gerente: str):
    """Testa o endpoint de criação com dados válidos (HTTP 201)"""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {
        "nome": "Suíte Presidencial",
        "descricao": "Quarto de luxo com vista mar",
        "precoBaseDiaria": 500.00,
        "capacidade": 4
    }

    response = await client.post("/tipos-quarto/", json=payload, headers=headers)

    assert response.status_code == 201
    dados = response.json()
    assert dados["nome"] == "Suíte Presidencial"
    assert "id" in dados


@pytest.mark.asyncio
async def test_api_criar_tipo_quarto_preco_invalido(client: AsyncClient, token_gerente: str):
    """O schema Pydantic deve barrar preços negativos ou zero (HTTP 422 Unprocessable Entity)"""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {
        "nome": "Quarto Errado",
        "precoBaseDiaria": -50.00,  # Valor inválido!
        "capacidade": 2
    }

    response = await client.post("/tipos-quarto/", json=payload, headers=headers)

    # O FastAPI devolve 422 quando a validação do Pydantic falha
    assert response.status_code == 422
    assert "precoBaseDiaria" in response.text


@pytest.mark.asyncio
async def test_api_criar_tipo_quarto_sem_token_retorna_401(client: AsyncClient):
    """Rota de tipos de quarto exige autenticação."""
    payload = {"nome": "Standard", "precoBaseDiaria": 100.0, "capacidade": 2}
    response = await client.post("/tipos-quarto/", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_criar_tipo_quarto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Apenas Gerentes podem criar tipos de quarto."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {"nome": "Standard", "precoBaseDiaria": 100.0, "capacidade": 2}
    response = await client.post("/tipos-quarto/", json=payload, headers=headers)
    assert response.status_code == 403
