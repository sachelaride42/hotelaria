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
    # 2. CHECK-OUT
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
