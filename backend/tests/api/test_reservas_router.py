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
