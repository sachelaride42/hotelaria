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


@pytest.mark.asyncio
async def test_api_atualizar_usuario_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente atualiza dados de outro usuário com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload_criar = {"nome": "Original", "email": "original@hotel.com", "senha": "123456", "tipo": "RECEPCIONISTA"}
    resp_criar = await client.post("/usuarios/", json=payload_criar, headers=headers)
    usuario_id = resp_criar.json()["id"]

    payload_update = {"nome": "Atualizado", "email": "atualizado@hotel.com", "tipo": "RECEPCIONISTA"}
    response = await client.put(f"/usuarios/{usuario_id}", json=payload_update, headers=headers)

    assert response.status_code == 200
    assert response.json()["nome"] == "Atualizado"
    assert response.json()["email"] == "atualizado@hotel.com"
    assert "senha" not in response.json()


@pytest.mark.asyncio
async def test_api_atualizar_usuario_com_nova_senha(client: AsyncClient, token_gerente: str):
    """Gerente pode alterar a senha de um usuário."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload_criar = {"nome": "Fulano", "email": "fulano@hotel.com", "senha": "senha_antiga", "tipo": "RECEPCIONISTA"}
    resp_criar = await client.post("/usuarios/", json=payload_criar, headers=headers)
    usuario_id = resp_criar.json()["id"]

    payload_update = {"nome": "Fulano", "email": "fulano@hotel.com", "tipo": "RECEPCIONISTA", "senha": "nova_senha_123"}
    response = await client.put(f"/usuarios/{usuario_id}", json=payload_update, headers=headers)

    assert response.status_code == 200
    login_resp = await client.post("/auth/login", data={"username": "fulano@hotel.com", "password": "nova_senha_123"})
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_api_atualizar_usuario_nao_encontrado_retorna_404(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload_update = {"nome": "Inexistente", "email": "x@hotel.com", "tipo": "RECEPCIONISTA"}
    response = await client.put("/usuarios/9999", json=payload_update, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_atualizar_usuario_sem_token_retorna_401(client: AsyncClient):
    payload_update = {"nome": "Qualquer", "email": "x@hotel.com", "tipo": "RECEPCIONISTA"}
    response = await client.put("/usuarios/1", json=payload_update)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_usuario_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente deleta um usuário com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload_criar = {"nome": "Temporario", "email": "temp@hotel.com", "senha": "123456", "tipo": "RECEPCIONISTA"}
    resp_criar = await client.post("/usuarios/", json=payload_criar, headers=headers)
    usuario_id = resp_criar.json()["id"]

    response = await client.delete(f"/usuarios/{usuario_id}", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_api_deletar_usuario_nao_encontrado_retorna_404(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.delete("/usuarios/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_deletar_usuario_sem_token_retorna_401(client: AsyncClient):
    response = await client.delete("/usuarios/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_usuario_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Recepcionista não pode deletar usuários."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.delete("/usuarios/1", headers=headers)
    assert response.status_code == 403


# --- GET /usuarios/ ---

@pytest.mark.asyncio
async def test_api_listar_usuarios_vazio(client: AsyncClient, token_gerente: str):
    """Lista retorna vazia quando não há usuários além do gerente de teste."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.get("/usuarios/", headers=headers)
    assert response.status_code == 200
    dados = response.json()
    assert isinstance(dados, list)
    assert len(dados) >= 1  # o gerente criado pelo fixture está presente


@pytest.mark.asyncio
async def test_api_listar_usuarios_com_registros(client: AsyncClient, token_gerente: str):
    """Após criar um recepcionista, ele aparece na listagem."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    await client.post("/usuarios/", json={"nome": "Recep Lista", "email": "rlista@hotel.com", "senha": "senha123", "tipo": "RECEPCIONISTA"}, headers=headers)

    response = await client.get("/usuarios/", headers=headers)
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert "rlista@hotel.com" in emails


@pytest.mark.asyncio
async def test_api_listar_usuarios_filtro_por_tipo(client: AsyncClient, token_gerente: str):
    """Filtro por tipo retorna apenas usuários do tipo indicado."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    await client.post("/usuarios/", json={"nome": "Recep Filtro", "email": "rfiltro@hotel.com", "senha": "senha123", "tipo": "RECEPCIONISTA"}, headers=headers)

    response = await client.get("/usuarios/?tipo=RECEPCIONISTA", headers=headers)
    assert response.status_code == 200
    tipos = [u["tipo"] for u in response.json()]
    assert all(t == "RECEPCIONISTA" for t in tipos)


@pytest.mark.asyncio
async def test_api_listar_usuarios_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/usuarios/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_listar_usuarios_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Apenas gerentes podem listar usuários."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.get("/usuarios/", headers=headers)
    assert response.status_code == 403


# --- GET /usuarios/{id} ---

@pytest.mark.asyncio
async def test_api_buscar_usuario_por_id_sucesso(client: AsyncClient, token_gerente: str):
    """Gerente busca usuário existente por ID."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp_criar = await client.post("/usuarios/", json={"nome": "Busca ID", "email": "buscaid@hotel.com", "senha": "senha123", "tipo": "RECEPCIONISTA"}, headers=headers)
    usuario_id = resp_criar.json()["id"]

    response = await client.get(f"/usuarios/{usuario_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "buscaid@hotel.com"


@pytest.mark.asyncio
async def test_api_buscar_usuario_por_id_inexistente_retorna_404(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.get("/usuarios/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_buscar_usuario_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/usuarios/1")
    assert response.status_code == 401
