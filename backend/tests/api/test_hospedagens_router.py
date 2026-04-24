import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
from backend.src.domain.models.quarto import StatusOcupacao, StatusLimpeza


@pytest_asyncio.fixture
async def setup_dados_iniciais(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Cria Cliente, TipoQuarto e Quarto para podermos testar a hospedagem."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    # 1. Cliente (qualquer usuário logado pode criar)
    cliente_resp = await client.post("/clientes/", json={"nome": "Carlos", "telefone": "123"}, headers=r_headers)
    # 2. Tipo Quarto (Diária R$ 100) — exige Gerente
    tipo_resp = await client.post("/tipos-quarto/", json={"nome": "Casal", "precoBaseDiaria": 100.00, "capacidade": 2}, headers=g_headers)
    # 3. Quarto 101 (Versão 1, LIVRE) — exige Gerente
    quarto_resp = await client.post("/quartos/",
                                    json={"numero": "101", "andar": 1, "tipo_quarto_id": tipo_resp.json()["id"]},
                                    headers=g_headers)

    return {
        "cliente_id": cliente_resp.json()["id"],
        "quarto_id": quarto_resp.json()["id"],
        "quarto_versao": quarto_resp.json()["versao"]
    }


@pytest.mark.asyncio
async def test_api_fluxo_checkin_e_checkout(client: AsyncClient, token_recepcionista: str, setup_dados_iniciais):
    dados = setup_dados_iniciais
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    data_saida_prevista = (datetime.now() + timedelta(days=2)).isoformat()

    # ==========================================
    # 1. CHECK-IN
    # ==========================================
    payload_checkin = {
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": data_saida_prevista,
        "versao_quarto": dados["quarto_versao"]
    }

    resp_checkin = await client.post("/hospedagens/checkin", json=payload_checkin, headers=r_headers)
    assert resp_checkin.status_code == 201
    hospedagem_id = resp_checkin.json()["id"]

    # Verifica se o quarto ficou OCUPADO
    resp_quarto_apos_checkin = await client.get(f"/quartos/{dados['quarto_id']}", headers=r_headers)
    print(resp_quarto_apos_checkin.json())
    assert resp_quarto_apos_checkin.json()["status_ocupacao"] == StatusOcupacao.OCUPADO.value
    nova_versao_quarto = resp_quarto_apos_checkin.json()["versao"]  # A versão subiu para 2!

    # ==========================================
    # 2. REGISTRAR PAGAMENTO (obrigatório antes do checkout)
    # ==========================================
    await client.post("/pagamentos/", json={
        "hospedagem_id": hospedagem_id,
        "valor_pago": 1000.00,  # valor alto para cobrir qualquer total calculado
        "forma_pagamento": "PIX"
    }, headers=r_headers)

    # ==========================================
    # 3. CHECK-OUT
    # ==========================================
    payload_checkout = {
        "versao_quarto": nova_versao_quarto
    }

    resp_checkout = await client.post(f"/hospedagens/{hospedagem_id}/checkout", json=payload_checkout, headers=r_headers)
    assert resp_checkout.status_code == 200
    assert resp_checkout.json()["status"] == "FINALIZADA"

    # Verifica se o quarto ficou LIVRE e SUJO para a equipe de limpeza
    resp_quarto_apos_checkout = await client.get(f"/quartos/{dados['quarto_id']}", headers=r_headers)
    assert resp_quarto_apos_checkout.json()["status_ocupacao"] == StatusOcupacao.LIVRE.value
    assert resp_quarto_apos_checkout.json()["status_limpeza"] == StatusLimpeza.SUJO.value


# ─── Checkout: validação de pagamento (ServicoCheckout) ──────────────────────

@pytest.mark.asyncio
async def test_api_checkout_sem_pagamento_retorna_400(client: AsyncClient, token_recepcionista: str, setup_dados_iniciais):
    """UC5: checkout sem nenhum pagamento registrado deve ser bloqueado (400)."""
    dados = setup_dados_iniciais
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    resp_checkin = await client.post("/hospedagens/checkin", json={
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=1)).isoformat(),
        "versao_quarto": dados["quarto_versao"]
    }, headers=r_headers)
    hospedagem_id = resp_checkin.json()["id"]

    versao = (await client.get(f"/quartos/{dados['quarto_id']}", headers=r_headers)).json()["versao"]

    resp = await client.post(
        f"/hospedagens/{hospedagem_id}/checkout",
        json={"versao_quarto": versao},
        headers=r_headers,
    )
    assert resp.status_code == 400
    assert "insuficiente" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_checkout_com_pagamento_parcial_retorna_400(client: AsyncClient, token_recepcionista: str, setup_dados_iniciais):
    """UC5: pagamento parcial (abaixo do total calculado) deve bloquear o checkout (400)."""
    dados = setup_dados_iniciais
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    resp_checkin = await client.post("/hospedagens/checkin", json={
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=1)).isoformat(),
        "versao_quarto": dados["quarto_versao"]
    }, headers=r_headers)
    hospedagem_id = resp_checkin.json()["id"]

    # Paga apenas R$0,01 — garante que será insuficiente para qualquer diária
    await client.post("/pagamentos/", json={
        "hospedagem_id": hospedagem_id,
        "valor_pago": 0.01,
        "forma_pagamento": "PIX"
    }, headers=r_headers)

    versao = (await client.get(f"/quartos/{dados['quarto_id']}", headers=r_headers)).json()["versao"]

    resp = await client.post(
        f"/hospedagens/{hospedagem_id}/checkout",
        json={"versao_quarto": versao},
        headers=r_headers,
    )
    assert resp.status_code == 400
    assert "insuficiente" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_checkout_com_pagamento_suficiente_finaliza_hospedagem(client: AsyncClient, token_recepcionista: str, setup_dados_iniciais):
    """UC5: pagamento que cobre o total calculado permite o checkout e libera o quarto."""
    dados = setup_dados_iniciais
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    resp_checkin = await client.post("/hospedagens/checkin", json={
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=1)).isoformat(),
        "versao_quarto": dados["quarto_versao"]
    }, headers=r_headers)
    hospedagem_id = resp_checkin.json()["id"]

    # Paga R$1.000 — suficiente para cobrir qualquer diária configurada no setup
    await client.post("/pagamentos/", json={
        "hospedagem_id": hospedagem_id,
        "valor_pago": 1000.00,
        "forma_pagamento": "CARTAO_CREDITO"
    }, headers=r_headers)

    versao = (await client.get(f"/quartos/{dados['quarto_id']}", headers=r_headers)).json()["versao"]

    resp = await client.post(
        f"/hospedagens/{hospedagem_id}/checkout",
        json={"versao_quarto": versao},
        headers=r_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "FINALIZADA"
    assert float(resp.json()["valor_total"]) > 0


@pytest.mark.asyncio
async def test_api_deletar_hospedagem_ativa_retorna_400(client: AsyncClient, token_gerente: str, setup_dados_iniciais):
    """Não é possível deletar uma hospedagem ATIVA — deve retornar 400."""
    dados = setup_dados_iniciais
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_gerente}"}

    payload_checkin = {
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
        "versao_quarto": dados["quarto_versao"]
    }
    resp_checkin = await client.post("/hospedagens/checkin", json=payload_checkin, headers=r_headers)
    hospedagem_id = resp_checkin.json()["id"]

    response = await client.delete(f"/hospedagens/{hospedagem_id}", headers=g_headers)
    assert response.status_code == 400
    assert "ativa" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_deletar_hospedagem_finalizada_sucesso(client: AsyncClient, token_gerente: str, setup_dados_iniciais):
    """Gerente deleta uma hospedagem FINALIZADA (após checkout) com sucesso."""
    dados = setup_dados_iniciais
    g_headers = {"Authorization": f"Bearer {token_gerente}"}

    payload_checkin = {
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
        "versao_quarto": dados["quarto_versao"]
    }
    resp_checkin = await client.post("/hospedagens/checkin", json=payload_checkin, headers=g_headers)
    hospedagem_id = resp_checkin.json()["id"]

    resp_quarto = await client.get(f"/quartos/{dados['quarto_id']}", headers=g_headers)
    versao_apos_checkin = resp_quarto.json()["versao"]

    # Registrar pagamento antes do checkout
    await client.post("/pagamentos/", json={
        "hospedagem_id": hospedagem_id,
        "valor_pago": 1000.00,
        "forma_pagamento": "DINHEIRO"
    }, headers=g_headers)

    await client.post(f"/hospedagens/{hospedagem_id}/checkout", json={"versao_quarto": versao_apos_checkin}, headers=g_headers)

    response = await client.delete(f"/hospedagens/{hospedagem_id}", headers=g_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_api_deletar_hospedagem_nao_encontrada_retorna_404(client: AsyncClient, token_gerente: str):
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.delete("/hospedagens/9999", headers=g_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_deletar_hospedagem_sem_token_retorna_401(client: AsyncClient):
    response = await client.delete("/hospedagens/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_deletar_hospedagem_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str):
    """Recepcionista não pode deletar hospedagens — exige Gerente."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.delete("/hospedagens/1", headers=r_headers)
    assert response.status_code == 403


# --- GET /hospedagens/ ---

@pytest.mark.asyncio
async def test_api_listar_hospedagens_vazio(client: AsyncClient, token_recepcionista: str):
    """Lista retorna vazia quando não há hospedagens."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.get("/hospedagens/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_api_listar_hospedagens_com_registros(client: AsyncClient, token_gerente: str, token_recepcionista: str, setup_dados_iniciais):
    """Após check-in, hospedagem aparece na listagem."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    dados = setup_dados_iniciais
    checkout_previsto = (datetime.now() + timedelta(days=2)).isoformat()
    payload_checkin = {"cliente_id": dados["cliente_id"], "quarto_id": dados["quarto_id"], "data_checkout_previsto": checkout_previsto, "versao_quarto": dados["quarto_versao"]}
    await client.post("/hospedagens/checkin", json=payload_checkin, headers=r_headers)

    response = await client.get("/hospedagens/", headers=r_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_api_listar_hospedagens_filtro_por_status(client: AsyncClient, token_gerente: str, token_recepcionista: str, setup_dados_iniciais):
    """Filtro por status retorna apenas hospedagens naquele estado."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    dados = setup_dados_iniciais
    checkout_previsto = (datetime.now() + timedelta(days=2)).isoformat()
    payload_checkin = {"cliente_id": dados["cliente_id"], "quarto_id": dados["quarto_id"], "data_checkout_previsto": checkout_previsto, "versao_quarto": dados["quarto_versao"]}
    await client.post("/hospedagens/checkin", json=payload_checkin, headers=r_headers)

    response = await client.get("/hospedagens/?status=ATIVA", headers=r_headers)
    assert response.status_code == 200
    assert all(h["status"] == "ATIVA" for h in response.json())


@pytest.mark.asyncio
async def test_api_listar_hospedagens_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/hospedagens/")
    assert response.status_code == 401


# --- GET /hospedagens/{id} ---

@pytest.mark.asyncio
async def test_api_buscar_hospedagem_por_id_sucesso(client: AsyncClient, token_gerente: str, token_recepcionista: str, setup_dados_iniciais):
    """Usuário logado busca hospedagem existente por ID."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    dados = setup_dados_iniciais
    checkout_previsto = (datetime.now() + timedelta(days=2)).isoformat()
    payload_checkin = {"cliente_id": dados["cliente_id"], "quarto_id": dados["quarto_id"], "data_checkout_previsto": checkout_previsto, "versao_quarto": dados["quarto_versao"]}
    resp = await client.post("/hospedagens/checkin", json=payload_checkin, headers=r_headers)
    hospedagem_id = resp.json()["id"]

    response = await client.get(f"/hospedagens/{hospedagem_id}", headers=r_headers)
    assert response.status_code == 200
    assert response.json()["id"] == hospedagem_id


@pytest.mark.asyncio
async def test_api_buscar_hospedagem_por_id_inexistente_retorna_404(client: AsyncClient, token_recepcionista: str):
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    response = await client.get("/hospedagens/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_buscar_hospedagem_sem_token_retorna_401(client: AsyncClient):
    response = await client.get("/hospedagens/1")
    assert response.status_code == 401


# ─── valor_diaria_negociado (UC5) ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_checkin_com_valor_negociado_persiste_campo(client: AsyncClient, token_recepcionista: str, setup_dados_iniciais):
    """Check-in com valor_diaria_negociado deve persistir o campo na hospedagem."""
    dados = setup_dados_iniciais
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    resp = await client.post("/hospedagens/checkin", json={
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
        "versao_quarto": dados["quarto_versao"],
        "valor_diaria_negociado": 150.00,
    }, headers=r_headers)

    assert resp.status_code == 201
    assert float(resp.json()["valor_diaria_negociado"]) == 150.0


@pytest.mark.asyncio
async def test_api_checkout_usa_valor_negociado(client: AsyncClient, token_recepcionista: str, setup_dados_iniciais):
    """Checkout deve calcular valor_total usando o preço negociado, não o preço base do tipo."""
    dados = setup_dados_iniciais
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    # Check-in com preço negociado R$150 (tipo base é R$100)
    resp_checkin = await client.post("/hospedagens/checkin", json={
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
        "versao_quarto": dados["quarto_versao"],
        "valor_diaria_negociado": 150.00,
    }, headers=r_headers)
    hospedagem_id = resp_checkin.json()["id"]

    versao = (await client.get(f"/quartos/{dados['quarto_id']}", headers=r_headers)).json()["versao"]

    await client.post("/pagamentos/", json={
        "hospedagem_id": hospedagem_id,
        "valor_pago": 1000.00,
        "forma_pagamento": "PIX",
    }, headers=r_headers)

    resp_checkout = await client.post(
        f"/hospedagens/{hospedagem_id}/checkout",
        json={"versao_quarto": versao},
        headers=r_headers,
    )
    assert resp_checkout.status_code == 200
    # valor_total deve ser >= R$150 (preço negociado), não R$100 (preço base do tipo)
    assert float(resp_checkout.json()["valor_total"]) >= 150.0


@pytest.mark.asyncio
async def test_api_checkout_sem_negociado_usa_preco_base(client: AsyncClient, token_recepcionista: str, setup_dados_iniciais):
    """Sem valor_diaria_negociado, checkout usa o preço base do tipo de quarto (regressão)."""
    dados = setup_dados_iniciais
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    # Check-in SEM valor_diaria_negociado
    resp_checkin = await client.post("/hospedagens/checkin", json={
        "cliente_id": dados["cliente_id"],
        "quarto_id": dados["quarto_id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
        "versao_quarto": dados["quarto_versao"],
    }, headers=r_headers)
    hospedagem_id = resp_checkin.json()["id"]
    assert resp_checkin.json()["valor_diaria_negociado"] is None

    versao = (await client.get(f"/quartos/{dados['quarto_id']}", headers=r_headers)).json()["versao"]

    await client.post("/pagamentos/", json={
        "hospedagem_id": hospedagem_id,
        "valor_pago": 1000.00,
        "forma_pagamento": "PIX",
    }, headers=r_headers)

    resp_checkout = await client.post(
        f"/hospedagens/{hospedagem_id}/checkout",
        json={"versao_quarto": versao},
        headers=r_headers,
    )
    assert resp_checkout.status_code == 200
    # valor_total deve usar R$100 (preço base) — checkout day use = 1 diária = R$100
    assert float(resp_checkout.json()["valor_total"]) >= 100.0
