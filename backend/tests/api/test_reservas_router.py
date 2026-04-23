import pytest
from httpx import AsyncClient
from datetime import date


@pytest.mark.asyncio
async def test_api_criar_reserva_e_disponibilidade(client: AsyncClient, token_gerente: str, token_recepcionista: str, db_session):
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    # Setup de dados no banco (usando as rotas para criar os pré-requisitos)
    await client.post("/clientes/", json={"nome": "Ana", "telefone": "123"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100, "capacidade": 1}, headers=g_headers)
    # Criamos APENAS 1 quarto físico do tipo 1
    await client.post("/quartos/", json={"numero": "100", "andar": 1, "tipo_quarto_id": 1}, headers=g_headers)

    payload_reserva = {
        "cliente_id": 1,
        "tipo_quarto_id": 1,
        "data_entrada": str(date(2026, 5, 1)),
        "data_saida": str(date(2026, 5, 5))
    }

    # Primeira reserva: Sucesso (Quarto está livre)
    resp1 = await client.post("/reservas/", json=payload_reserva, headers=r_headers)
    assert resp1.status_code == 201

    # Segunda reserva para AS MESMAS DATAS: Deve dar erro 409 (Overbooking)
    resp2 = await client.post("/reservas/", json=payload_reserva, headers=r_headers)
    assert resp2.status_code == 409
    assert "Não há quartos disponíveis" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_api_criar_reserva_e_disponibilidade2(client: AsyncClient, token_gerente: str, token_recepcionista: str, db_session):
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    r1 = await client.post("/clientes/", json={"nome": "Ana", "telefone": "123"}, headers=r_headers)
    assert r1.status_code == 201, r1.json()

    r2 = await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100, "capacidade": 1}, headers=g_headers)
    assert r2.status_code == 201, r2.json()

    r3 = await client.post("/quartos/", json={"numero": "100", "andar": 1, "tipo_quarto_id": 1}, headers=g_headers)
    assert r3.status_code == 201, r3.json()

    payload_reserva = {
        "cliente_id": 1,
        "tipo_quarto_id": 1,
        "data_entrada": str(date(2026, 5, 1)),
        "data_saida": str(date(2026, 5, 5))
    }

    resp1 = await client.post("/reservas/", json=payload_reserva, headers=r_headers)
    print(resp1.json())
    assert resp1.status_code == 201


@pytest.mark.asyncio
async def test_api_atualizar_reserva_sucesso(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Qualquer usuário logado pode atualizar as datas de uma reserva CONFIRMADA."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    await client.post("/clientes/", json={"nome": "Ana", "telefone": "123"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100, "capacidade": 1}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "100", "andar": 1, "tipo_quarto_id": 1}, headers=g_headers)

    payload_reserva = {"cliente_id": 1, "tipo_quarto_id": 1,
                       "data_entrada": str(date(2027, 6, 1)), "data_saida": str(date(2027, 6, 5))}
    resp = await client.post("/reservas/", json=payload_reserva, headers=r_headers)
    reserva_id = resp.json()["id"]

    payload_update = {"data_entrada": str(date(2027, 7, 1)), "data_saida": str(date(2027, 7, 10))}
    response = await client.put(f"/reservas/{reserva_id}", json=payload_update, headers=r_headers)

    assert response.status_code == 200
    assert response.json()["data_entrada"] == str(date(2027, 7, 1))
    assert response.json()["data_saida"] == str(date(2027, 7, 10))


@pytest.mark.asyncio
async def test_api_atualizar_reserva_nao_encontrada_retorna_404(client: AsyncClient, token_recepcionista: str):
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload_update = {"data_entrada": str(date(2027, 7, 1)), "data_saida": str(date(2027, 7, 10))}
    response = await client.put("/reservas/9999", json=payload_update, headers=r_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_atualizar_reserva_sem_token_retorna_401(client: AsyncClient):
    payload_update = {"data_entrada": str(date(2027, 7, 1)), "data_saida": str(date(2027, 7, 10))}
    response = await client.put("/reservas/1", json=payload_update)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_reserva_sucesso(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Gerente deleta uma reserva CONFIRMADA com sucesso."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    await client.post("/clientes/", json={"nome": "Bob", "telefone": "456"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Duplo", "precoBaseDiaria": 150, "capacidade": 2}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "200", "andar": 2, "tipo_quarto_id": 1}, headers=g_headers)

    payload_reserva = {"cliente_id": 1, "tipo_quarto_id": 1,
                       "data_entrada": str(date(2027, 8, 1)), "data_saida": str(date(2027, 8, 5))}
    resp = await client.post("/reservas/", json=payload_reserva, headers=r_headers)
    reserva_id = resp.json()["id"]

    response = await client.delete(f"/reservas/{reserva_id}", headers=g_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_api_deletar_reserva_nao_encontrada_retorna_404(client: AsyncClient, token_gerente: str):
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.delete("/reservas/9999", headers=g_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_deletar_reserva_sem_token_retorna_401(client: AsyncClient):
    response = await client.delete("/reservas/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_reserva_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Recepcionista não pode deletar reservas — exige Gerente."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.delete("/reservas/1", headers=r_headers)
    assert response.status_code == 403


# --- GET /reservas/ ---

@pytest.mark.asyncio
async def test_api_listar_reservas_vazio(client: AsyncClient, token_recepcionista: str):
    """Lista retorna vazia quando não há reservas."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.get("/reservas/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_api_listar_reservas_com_registros(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Reservas criadas aparecem na listagem."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    await client.post("/clientes/", json={"nome": "Ana", "telefone": "123"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100, "capacidade": 1}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "100", "andar": 1, "tipo_quarto_id": 1}, headers=g_headers)
    await client.post("/reservas/", json={"cliente_id": 1, "tipo_quarto_id": 1, "data_entrada": str(date(2027, 5, 1)), "data_saida": str(date(2027, 5, 5))}, headers=r_headers)

    response = await client.get("/reservas/", headers=r_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_api_listar_reservas_filtro_por_cliente(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Filtro por cliente_id retorna apenas reservas daquele cliente."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    await client.post("/clientes/", json={"nome": "Cliente1", "telefone": "1"}, headers=r_headers)
    await client.post("/clientes/", json={"nome": "Cliente2", "telefone": "2"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100, "capacidade": 2}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "110", "andar": 1, "tipo_quarto_id": 1}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "111", "andar": 1, "tipo_quarto_id": 1}, headers=g_headers)
    await client.post("/reservas/", json={"cliente_id": 1, "tipo_quarto_id": 1, "data_entrada": str(date(2027, 5, 1)), "data_saida": str(date(2027, 5, 3))}, headers=r_headers)
    await client.post("/reservas/", json={"cliente_id": 2, "tipo_quarto_id": 1, "data_entrada": str(date(2027, 6, 1)), "data_saida": str(date(2027, 6, 3))}, headers=r_headers)

    response = await client.get("/reservas/?cliente_id=1", headers=r_headers)
    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 1
    assert dados[0]["cliente_id"] == 1


@pytest.mark.asyncio
async def test_api_listar_reservas_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/reservas/")
    assert response.status_code == 401


# --- GET /reservas/{id} ---

@pytest.mark.asyncio
async def test_api_buscar_reserva_por_id_sucesso(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Usuário logado busca reserva existente por ID."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    await client.post("/clientes/", json={"nome": "Ana", "telefone": "123"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100, "capacidade": 1}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "100", "andar": 1, "tipo_quarto_id": 1}, headers=g_headers)
    resp = await client.post("/reservas/", json={"cliente_id": 1, "tipo_quarto_id": 1, "data_entrada": str(date(2027, 5, 1)), "data_saida": str(date(2027, 5, 5))}, headers=r_headers)
    reserva_id = resp.json()["id"]

    response = await client.get(f"/reservas/{reserva_id}", headers=r_headers)
    assert response.status_code == 200
    assert response.json()["id"] == reserva_id


@pytest.mark.asyncio
async def test_api_buscar_reserva_por_id_inexistente_retorna_404(client: AsyncClient, token_recepcionista: str):
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.get("/reservas/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_buscar_reserva_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/reservas/1")
    assert response.status_code == 401


# --- POST /reservas/lista-espera/ ---

@pytest.mark.asyncio
async def test_api_criar_reserva_lista_espera_sucesso(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Reserva criada em lista de espera deve ter status LISTA_ESPERA, mesmo sem disponibilidade."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    await client.post("/clientes/", json={"nome": "Carlos", "telefone": "789"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Simples", "precoBaseDiaria": 100, "capacidade": 1}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "300", "andar": 3, "tipo_quarto_id": 1}, headers=g_headers)

    # Ocupa o único quarto disponível
    payload = {"cliente_id": 1, "tipo_quarto_id": 1, "data_entrada": str(date(2028, 1, 1)), "data_saida": str(date(2028, 1, 5))}
    await client.post("/reservas/", json=payload, headers=r_headers)

    # Lista de espera deve funcionar mesmo sem vagas
    response = await client.post("/reservas/lista-espera/", json=payload, headers=r_headers)
    assert response.status_code == 201
    assert response.json()["status"] == "LISTA_ESPERA"


@pytest.mark.asyncio
async def test_api_criar_reserva_lista_espera_tipo_inexistente_retorna_404(client: AsyncClient, token_recepcionista: str):
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {"cliente_id": 1, "tipo_quarto_id": 9999, "data_entrada": str(date(2028, 2, 1)), "data_saida": str(date(2028, 2, 5))}
    response = await client.post("/reservas/lista-espera/", json=payload, headers=r_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_criar_reserva_lista_espera_sem_token_retorna_401(client: AsyncClient):
    payload = {"cliente_id": 1, "tipo_quarto_id": 1, "data_entrada": str(date(2028, 3, 1)), "data_saida": str(date(2028, 3, 5))}
    response = await client.post("/reservas/lista-espera/", json=payload)
    assert response.status_code == 401


# --- PATCH /reservas/{id}/cancelar ---

@pytest.mark.asyncio
async def test_api_cancelar_reserva_sucesso(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Reserva CONFIRMADA pode ser cancelada."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    await client.post("/clientes/", json={"nome": "Diana", "telefone": "321"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Standard", "precoBaseDiaria": 120, "capacidade": 2}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "400", "andar": 4, "tipo_quarto_id": 1}, headers=g_headers)

    payload = {"cliente_id": 1, "tipo_quarto_id": 1, "data_entrada": str(date(2028, 4, 1)), "data_saida": str(date(2028, 4, 5))}
    resp = await client.post("/reservas/", json=payload, headers=r_headers)
    reserva_id = resp.json()["id"]

    response = await client.patch(f"/reservas/{reserva_id}/cancelar", headers=r_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELADA"


@pytest.mark.asyncio
async def test_api_cancelar_reserva_nao_encontrada_retorna_404(client: AsyncClient, token_recepcionista: str):
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.patch("/reservas/9999/cancelar", headers=r_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_cancelar_reserva_sem_token_retorna_401(client: AsyncClient):
    response = await client.patch("/reservas/1/cancelar")
    assert response.status_code == 401


# --- GET /reservas/disponibilidade/ ---

@pytest.mark.asyncio
async def test_api_verificar_disponibilidade_com_vaga(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Endpoint retorna disponível quando há quartos livres no período."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    await client.post("/tipos-quarto/", json={"nome": "Disponivel", "precoBaseDiaria": 80, "capacidade": 1}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "500", "andar": 5, "tipo_quarto_id": 1}, headers=g_headers)

    response = await client.get(
        "/reservas/disponibilidade/?tipo_quarto_id=1&data_entrada=2029-01-01&data_saida=2029-01-05",
        headers=r_headers
    )
    assert response.status_code == 200
    dados = response.json()
    assert dados["disponivel"] is True
    assert dados["quartos_livres"] >= 1


@pytest.mark.asyncio
async def test_api_verificar_disponibilidade_sem_vaga(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Endpoint retorna indisponível quando único quarto já está reservado no período."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    await client.post("/clientes/", json={"nome": "Eva", "telefone": "654"}, headers=r_headers)
    await client.post("/tipos-quarto/", json={"nome": "Lotado", "precoBaseDiaria": 90, "capacidade": 1}, headers=g_headers)
    await client.post("/quartos/", json={"numero": "600", "andar": 6, "tipo_quarto_id": 1}, headers=g_headers)

    payload = {"cliente_id": 1, "tipo_quarto_id": 1, "data_entrada": str(date(2029, 2, 1)), "data_saida": str(date(2029, 2, 5))}
    await client.post("/reservas/", json=payload, headers=r_headers)

    response = await client.get(
        "/reservas/disponibilidade/?tipo_quarto_id=1&data_entrada=2029-02-01&data_saida=2029-02-05",
        headers=r_headers
    )
    assert response.status_code == 200
    assert response.json()["disponivel"] is False


@pytest.mark.asyncio
async def test_api_verificar_disponibilidade_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/reservas/disponibilidade/?tipo_quarto_id=1&data_entrada=2029-03-01&data_saida=2029-03-05")
    assert response.status_code == 401
