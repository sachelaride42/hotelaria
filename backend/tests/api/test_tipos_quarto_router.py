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


@pytest.mark.asyncio
async def test_api_atualizar_tipo_quarto_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente atualiza um tipo de quarto com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/tipos-quarto/", json={"nome": "Executivo", "precoBaseDiaria": 200.0, "capacidade": 2}, headers=headers)
    tipo_id = resp.json()["id"]

    payload_update = {"nome": "Executivo Plus", "precoBaseDiaria": 250.0, "capacidade": 3}
    response = await client.put(f"/tipos-quarto/{tipo_id}", json=payload_update, headers=headers)

    assert response.status_code == 200
    assert response.json()["nome"] == "Executivo Plus"
    assert float(response.json()["precoBaseDiaria"]) == 250.0


@pytest.mark.asyncio
async def test_api_atualizar_tipo_quarto_nao_encontrado(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.put("/tipos-quarto/9999", json={"nome": "X", "precoBaseDiaria": 100.0, "capacidade": 1}, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_atualizar_tipo_quarto_sem_token_retorna_401(client: AsyncClient):
    response = await client.put("/tipos-quarto/1", json={"nome": "X", "precoBaseDiaria": 100.0, "capacidade": 1})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_tipo_quarto_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente deleta um tipo de quarto sem quartos vinculados."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/tipos-quarto/", json={"nome": "Para Deletar", "precoBaseDiaria": 50.0, "capacidade": 1}, headers=headers)
    tipo_id = resp.json()["id"]

    response = await client.delete(f"/tipos-quarto/{tipo_id}", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_api_deletar_tipo_quarto_com_quartos_retorna_409(client: AsyncClient, token_gerente: str):
    """Tipo com quartos físicos vinculados não pode ser removido — FK constraint → 409."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp_tipo = await client.post("/tipos-quarto/", json={"nome": "Vinculado", "precoBaseDiaria": 100.0, "capacidade": 2}, headers=headers)
    tipo_id = resp_tipo.json()["id"]
    await client.post("/quartos/", json={"numero": "900", "andar": 9, "tipo_quarto_id": tipo_id}, headers=headers)

    response = await client.delete(f"/tipos-quarto/{tipo_id}", headers=headers)
    assert response.status_code == 409
    assert "quartos físicos" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_deletar_tipo_quarto_nao_encontrado(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.delete("/tipos-quarto/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_deletar_tipo_quarto_sem_token_retorna_401(client: AsyncClient):
    response = await client.delete("/tipos-quarto/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_tipo_quarto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.delete("/tipos-quarto/1", headers=headers)
    assert response.status_code == 403


# --- GET /tipos-quarto/ ---

@pytest.mark.asyncio
async def test_api_listar_tipos_quarto_vazio(client: AsyncClient, token_gerente: str):
    """Lista retorna vazia quando não há tipos cadastrados."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.get("/tipos-quarto/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_api_listar_tipos_quarto_com_registros(client: AsyncClient, token_gerente: str):
    """Após criar tipos, eles aparecem na listagem."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    await client.post("/tipos-quarto/", json={"nome": "Standard", "precoBaseDiaria": 100.0, "capacidade": 2}, headers=headers)
    await client.post("/tipos-quarto/", json={"nome": "Suite", "precoBaseDiaria": 300.0, "capacidade": 4}, headers=headers)

    response = await client.get("/tipos-quarto/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_api_listar_tipos_quarto_filtro_capacidade(client: AsyncClient, token_gerente: str):
    """Filtro por capacidade_minima retorna apenas tipos compatíveis."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100.0, "capacidade": 1}, headers=headers)
    await client.post("/tipos-quarto/", json={"nome": "Familia", "precoBaseDiaria": 200.0, "capacidade": 4}, headers=headers)

    response = await client.get("/tipos-quarto/?capacidade_minima=3", headers=headers)
    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 1
    assert dados[0]["nome"] == "Familia"


@pytest.mark.asyncio
async def test_api_listar_tipos_quarto_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/tipos-quarto/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_listar_tipos_quarto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Apenas gerentes podem listar tipos de quarto."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.get("/tipos-quarto/", headers=headers)
    assert response.status_code == 403


# --- GET /tipos-quarto/{id} ---

@pytest.mark.asyncio
async def test_api_buscar_tipo_quarto_por_id_sucesso(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/tipos-quarto/", json={"nome": "Executivo", "precoBaseDiaria": 250.0, "capacidade": 2}, headers=headers)
    tipo_id = resp.json()["id"]

    response = await client.get(f"/tipos-quarto/{tipo_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["nome"] == "Executivo"


@pytest.mark.asyncio
async def test_api_buscar_tipo_quarto_por_id_inexistente_retorna_404(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.get("/tipos-quarto/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_buscar_tipo_quarto_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/tipos-quarto/1")
    assert response.status_code == 401
