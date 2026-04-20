import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_criar_produto_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente cria produto no catálogo com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {
        "descricao": "Sanduíche Natural",
        "preco_padrao": 18.50,
        "categoria": "PRODUTO"
    }

    response = await client.post("/catalogo/", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["descricao"] == "Sanduíche Natural"
    assert response.json()["id"] is not None


@pytest.mark.asyncio
async def test_api_criar_produto_duplicado_retorna_409(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {
        "descricao": "Café Expresso",
        "preco_padrao": 5.00,
        "categoria": "PRODUTO"
    }

    # 1. Cria a primeira vez com sucesso
    await client.post("/catalogo/", json=payload, headers=headers)

    # 2. Tenta criar de novo com o mesmo nome
    response = await client.post("/catalogo/", json=payload, headers=headers)

    assert response.status_code == 409
    assert "Já existe um produto" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_criar_produto_preco_negativo_retorna_422(client: AsyncClient, token_gerente: str):
    """O schema Pydantic (`condecimal`) deve bloquear isto na porta da API."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {
        "descricao": "Suco",
        "preco_padrao": -10.00,  # Valor inválido
        "categoria": "PRODUTO"
    }

    response = await client.post("/catalogo/", json=payload, headers=headers)

    assert response.status_code == 422
    assert "preco_padrao" in response.text


@pytest.mark.asyncio
async def test_api_listar_catalogo(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Qualquer usuário logado pode listar o catálogo."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    # Setup: gerente insere dois itens
    await client.post("/catalogo/", json={"descricao": "Água", "preco_padrao": 4.0, "categoria": "PRODUTO"}, headers=g_headers)
    await client.post("/catalogo/", json={"descricao": "Massagem", "preco_padrao": 150.0, "categoria": "SERVICO"}, headers=g_headers)

    # Recepcionista consegue listar
    response = await client.get("/catalogo/", headers=r_headers)

    assert response.status_code == 200
    lista = response.json()
    assert len(lista) == 2
    assert lista[0]["descricao"] == "Água"
    assert lista[1]["descricao"] == "Massagem"


@pytest.mark.asyncio
async def test_api_criar_produto_sem_token_retorna_401(client: AsyncClient):
    """Catálogo exige autenticação."""
    payload = {"descricao": "Chá", "preco_padrao": 3.0, "categoria": "PRODUTO"}
    response = await client.post("/catalogo/", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_criar_produto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Apenas Gerentes podem adicionar itens ao catálogo."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {"descricao": "Chá", "preco_padrao": 3.0, "categoria": "PRODUTO"}
    response = await client.post("/catalogo/", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_api_atualizar_produto_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente atualiza um item do catálogo com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/catalogo/", json={"descricao": "Original", "preco_padrao": 10.0, "categoria": "PRODUTO"}, headers=headers)
    item_id = resp.json()["id"]

    payload_update = {"descricao": "Atualizado", "preco_padrao": 15.0, "categoria": "SERVICO"}
    response = await client.put(f"/catalogo/{item_id}", json=payload_update, headers=headers)

    assert response.status_code == 200
    assert response.json()["descricao"] == "Atualizado"
    assert float(response.json()["preco_padrao"]) == 15.0
    assert response.json()["categoria"] == "SERVICO"


@pytest.mark.asyncio
async def test_api_atualizar_produto_nao_encontrado_retorna_404(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.put("/catalogo/9999", json={"descricao": "Qualquer", "preco_padrao": 1.0, "categoria": "PRODUTO"}, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_atualizar_produto_sem_token_retorna_401(client: AsyncClient):
    response = await client.put("/catalogo/1", json={"descricao": "Qualquer", "preco_padrao": 1.0, "categoria": "PRODUTO"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_atualizar_produto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.put("/catalogo/1", json={"descricao": "Qualquer", "preco_padrao": 1.0, "categoria": "PRODUTO"}, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_api_deletar_produto_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente deleta um item do catálogo com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/catalogo/", json={"descricao": "Para Deletar", "preco_padrao": 5.0, "categoria": "PRODUTO"}, headers=headers)
    item_id = resp.json()["id"]

    response = await client.delete(f"/catalogo/{item_id}", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_api_deletar_produto_nao_encontrado_retorna_404(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.delete("/catalogo/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_deletar_produto_sem_token_retorna_401(client: AsyncClient):
    response = await client.delete("/catalogo/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_produto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.delete("/catalogo/1", headers=headers)
    assert response.status_code == 403
