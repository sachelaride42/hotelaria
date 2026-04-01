import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_criar_produto_sucesso(client: AsyncClient):
    payload = {
        "descricao": "Sanduíche Natural",
        "preco_padrao": 18.50,
        "categoria": "PRODUTO"
    }

    response = await client.post("/catalogo/", json=payload)

    assert response.status_code == 201
    assert response.json()["descricao"] == "Sanduíche Natural"
    assert response.json()["id"] is not None


@pytest.mark.asyncio
async def test_api_criar_produto_duplicado_retorna_409(client: AsyncClient):
    payload = {
        "descricao": "Café Expresso",
        "preco_padrao": 5.00,
        "categoria": "PRODUTO"
    }

    # 1. Cria a primeira vez com sucesso
    await client.post("/catalogo/", json=payload)

    # 2. Tenta criar de novo com o mesmo nome
    response = await client.post("/catalogo/", json=payload)

    assert response.status_code == 409
    assert "Já existe um produto" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_criar_produto_preco_negativo_retorna_422(client: AsyncClient):
    """O schema Pydantic (`condecimal`) deve bloquear isto na porta da API."""
    payload = {
        "descricao": "Suco",
        "preco_padrao": -10.00,  # Valor inválido
        "categoria": "PRODUTO"
    }

    response = await client.post("/catalogo/", json=payload)

    assert response.status_code == 422
    assert "preco_padrao" in response.text


@pytest.mark.asyncio
async def test_api_listar_catalogo(client: AsyncClient):
    # Setup: insere dois itens
    await client.post("/catalogo/", json={"descricao": "Água", "preco_padrao": 4.0, "categoria": "PRODUTO"})
    await client.post("/catalogo/", json={"descricao": "Massagem", "preco_padrao": 150.0, "categoria": "SERVICO"})

    # Act: Busca a lista
    response = await client.get("/catalogo/")

    assert response.status_code == 200
    lista = response.json()
    assert len(lista) == 2
    # Verifica se a ordenação alfabética está a funcionar via API
    assert lista[0]["descricao"] == "Água"
    assert lista[1]["descricao"] == "Massagem"