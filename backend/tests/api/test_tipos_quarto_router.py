import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_criar_tipo_quarto_sucesso(client: AsyncClient):
    """Testa o endpoint de criação com dados válidos (HTTP 201)"""
    payload = {
        "nome": "Suíte Presidencial",
        "descricao": "Quarto de luxo com vista mar",
        "precoBaseDiaria": 500.00,
        "capacidade": 4
    }

    response = await client.post("/tipos-quarto/", json=payload)

    assert response.status_code == 201
    dados = response.json()
    assert dados["nome"] == "Suíte Presidencial"
    assert "id" in dados


@pytest.mark.asyncio
async def test_api_criar_tipo_quarto_preco_invalido(client: AsyncClient):
    """O schema Pydantic deve barrar preços negativos ou zero (HTTP 422 Unprocessable Entity)"""
    payload = {
        "nome": "Quarto Errado",
        "precoBaseDiaria": -50.00,  # Valor inválido!
        "capacidade": 2
    }

    response = await client.post("/tipos-quarto/", json=payload)

    # O FastAPI devolve 422 quando a validação do Pydantic falha
    assert response.status_code == 422
    assert "precoBaseDiaria" in response.text