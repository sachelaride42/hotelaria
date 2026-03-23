import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
from backend.src.domain.models.quarto import StatusQuarto


@pytest_asyncio.fixture
async def setup_dados_iniciais(client: AsyncClient):
    """Cria Cliente, TipoQuarto e Quarto para podermos testar a hospedagem."""
    # 1. Cliente
    cliente_resp = await client.post("/clientes/", json={"nome": "Carlos", "telefone": "123"})
    # 2. Tipo Quarto (Diária R$ 100)
    tipo_resp = await client.post("/tipos-quarto/", json={"nome": "Casal", "precoBaseDiaria": 100.00, "capacidade": 2})
    # 3. Quarto 101 (Versão 1, LIVRE)
    quarto_resp = await client.post("/quartos/",
                                    json={"numero": "101", "andar": 1, "tipo_quarto_id": tipo_resp.json()["id"]})

    return {
        "cliente_id": cliente_resp.json()["id"],
        "quarto_id": quarto_resp.json()["id"],
        "quarto_versao": quarto_resp.json()["versao"]
    }


@pytest.mark.asyncio
async def test_api_fluxo_checkin_e_checkout(client: AsyncClient, setup_dados_iniciais):
    dados = setup_dados_iniciais
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

    resp_checkin = await client.post("/hospedagens/checkin", json=payload_checkin)
    assert resp_checkin.status_code == 201
    hospedagem_id = resp_checkin.json()["id"]

    # Verifica se o quarto ficou OCUPADO
    resp_quarto_apos_checkin = await client.get(f"/quartos/{dados['quarto_id']}")
    print(resp_quarto_apos_checkin.json())
    assert resp_quarto_apos_checkin.json()["status"] == StatusQuarto.OCUPADO.value
    nova_versao_quarto = resp_quarto_apos_checkin.json()["versao"]  # A versão subiu para 2!

    # ==========================================
    # 2. CHECK-OUT
    # ==========================================
    payload_checkout = {
        "versao_quarto": nova_versao_quarto
    }

    resp_checkout = await client.post(f"/hospedagens/{hospedagem_id}/checkout", json=payload_checkout)
    assert resp_checkout.status_code == 200
    assert resp_checkout.json()["status"] == "FINALIZADA"

    # Verifica se o quarto ficou SUJO para a equipe de limpeza
    resp_quarto_apos_checkout = await client.get(f"/quartos/{dados['quarto_id']}")
    assert resp_quarto_apos_checkout.json()["status"] == StatusQuarto.SUJO.value