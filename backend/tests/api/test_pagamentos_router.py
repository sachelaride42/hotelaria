import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest_asyncio.fixture
async def setup_hospedagem_ativa(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Cria todo o setup necessário e retorna uma hospedagem ATIVA."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    cliente_resp = await client.post(
        "/clientes/", json={"nome": "Ana Teste", "telefone": "999"}, headers=r_headers
    )
    tipo_resp = await client.post(
        "/tipos-quarto/",
        json={"nome": "Standard", "precoBaseDiaria": 100.00, "capacidade": 1},
        headers=g_headers,
    )
    quarto_resp = await client.post(
        "/quartos/",
        json={"numero": "201", "andar": 2, "tipo_quarto_id": tipo_resp.json()["id"]},
        headers=g_headers,
    )

    checkin_resp = await client.post(
        "/hospedagens/checkin",
        json={
            "cliente_id": cliente_resp.json()["id"],
            "quarto_id": quarto_resp.json()["id"],
            "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
            "versao_quarto": quarto_resp.json()["versao"],
        },
        headers=r_headers,
    )

    return {
        "hospedagem_id": checkin_resp.json()["id"],
        "quarto_id": quarto_resp.json()["id"],
        "r_headers": r_headers,
        "g_headers": g_headers,
    }


# ─── POST /pagamentos/ ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_registrar_pagamento_sucesso(client: AsyncClient, setup_hospedagem_ativa):
    """Registrar pagamento em hospedagem ATIVA retorna 201."""
    dados = setup_hospedagem_ativa
    payload = {
        "hospedagem_id": dados["hospedagem_id"],
        "valor_pago": 150.00,
        "forma_pagamento": "PIX",
    }
    resp = await client.post("/pagamentos/", json=payload, headers=dados["r_headers"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["hospedagem_id"] == dados["hospedagem_id"]
    assert float(body["valor_pago"]) == 150.00
    assert body["forma_pagamento"] == "PIX"
    assert "id" in body


@pytest.mark.asyncio
async def test_registrar_pagamento_hospedagem_inexistente_retorna_404(
    client: AsyncClient, token_recepcionista: str
):
    """Hospedagem que não existe deve retornar 404."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    resp = await client.post(
        "/pagamentos/",
        json={"hospedagem_id": 9999, "valor_pago": 100.00, "forma_pagamento": "DINHEIRO"},
        headers=r_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_registrar_pagamento_hospedagem_finalizada_retorna_400(
    client: AsyncClient, setup_hospedagem_ativa
):
    """Hospedagem já finalizada não deve aceitar novos pagamentos."""
    dados = setup_hospedagem_ativa

    # Pagar o suficiente e finalizar
    await client.post(
        "/pagamentos/",
        json={"hospedagem_id": dados["hospedagem_id"], "valor_pago": 1000.00, "forma_pagamento": "CARTAO_CREDITO"},
        headers=dados["r_headers"],
    )
    quarto_resp = await client.get(f"/quartos/{dados['quarto_id']}", headers=dados["r_headers"])
    versao = quarto_resp.json()["versao"]
    await client.post(
        f"/hospedagens/{dados['hospedagem_id']}/checkout",
        json={"versao_quarto": versao},
        headers=dados["r_headers"],
    )

    # Tentar novo pagamento na hospedagem finalizada
    resp = await client.post(
        "/pagamentos/",
        json={"hospedagem_id": dados["hospedagem_id"], "valor_pago": 50.00, "forma_pagamento": "PIX"},
        headers=dados["r_headers"],
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_registrar_pagamento_valor_zero_retorna_422(
    client: AsyncClient, setup_hospedagem_ativa
):
    """Valor zero é rejeitado pelo schema Pydantic (gt=0) com 422."""
    dados = setup_hospedagem_ativa
    resp = await client.post(
        "/pagamentos/",
        json={"hospedagem_id": dados["hospedagem_id"], "valor_pago": 0.00, "forma_pagamento": "DINHEIRO"},
        headers=dados["r_headers"],
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_registrar_pagamento_sem_token_retorna_401(client: AsyncClient):
    """Rota de pagamentos exige autenticação."""
    resp = await client.post(
        "/pagamentos/",
        json={"hospedagem_id": 1, "valor_pago": 100.00, "forma_pagamento": "PIX"},
    )
    assert resp.status_code == 401


# ─── GET /pagamentos/hospedagem/{id} ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_pagamentos_hospedagem(client: AsyncClient, setup_hospedagem_ativa):
    """Deve retornar todos os pagamentos registrados para a hospedagem."""
    dados = setup_hospedagem_ativa
    hid = dados["hospedagem_id"]

    # Registra dois pagamentos
    await client.post("/pagamentos/", json={"hospedagem_id": hid, "valor_pago": 50.00, "forma_pagamento": "PIX"}, headers=dados["r_headers"])
    await client.post("/pagamentos/", json={"hospedagem_id": hid, "valor_pago": 80.00, "forma_pagamento": "DINHEIRO"}, headers=dados["r_headers"])

    resp = await client.get(f"/pagamentos/hospedagem/{hid}", headers=dados["r_headers"])
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_listar_pagamentos_hospedagem_vazia(client: AsyncClient, setup_hospedagem_ativa):
    """Hospedagem sem pagamentos deve retornar lista vazia."""
    dados = setup_hospedagem_ativa
    resp = await client.get(f"/pagamentos/hospedagem/{dados['hospedagem_id']}", headers=dados["r_headers"])
    assert resp.status_code == 200
    assert resp.json() == []


# ─── DELETE /pagamentos/{id} ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deletar_pagamento_gerente_sucesso(client: AsyncClient, setup_hospedagem_ativa):
    """Gerente pode remover pagamento de hospedagem ATIVA."""
    dados = setup_hospedagem_ativa
    resp_criar = await client.post(
        "/pagamentos/",
        json={"hospedagem_id": dados["hospedagem_id"], "valor_pago": 100.00, "forma_pagamento": "PIX"},
        headers=dados["g_headers"],
    )
    pagamento_id = resp_criar.json()["id"]

    resp_del = await client.delete(f"/pagamentos/{pagamento_id}", headers=dados["g_headers"])
    assert resp_del.status_code == 204




@pytest.mark.asyncio
async def test_deletar_pagamento_inexistente_retorna_404(client: AsyncClient, token_gerente: str):
    """DELETE de pagamento que não existe retorna 404."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.delete("/pagamentos/9999", headers=g_headers)
    assert resp.status_code == 404
