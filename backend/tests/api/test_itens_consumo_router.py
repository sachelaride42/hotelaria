import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_api_lancar_consumo_hospedagem_inexistente(client: AsyncClient, token_recepcionista: str):
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {
        "hospedagem_id": 9999,  # Não existe no banco
        "descricao": "Chocolate",
        "quantidade": 1,
        "valor_unitario": 10.00
    }

    response = await client.post("/itens-consumo/", json=payload, headers=r_headers)

    assert response.status_code == 404
    assert "Hospedagem não encontrada" in response.json()["detail"]


@pytest_asyncio.fixture
async def hospedagem_ativa_id(client: AsyncClient, token_gerente: str, token_recepcionista: str):
    """Faz o setup completo via API até ter um Check-in ativo para receber consumos."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    resp_cli = await client.post("/clientes/", json={"nome": "Ana", "telefone": "321"}, headers=r_headers)
    resp_tipo = await client.post("/tipos-quarto/", json={"nome": "Luxo", "precoBaseDiaria": 200.0, "capacidade": 2}, headers=g_headers)
    resp_quarto = await client.post("/quartos/",
                                    json={"numero": "505", "andar": 5, "tipo_quarto_id": resp_tipo.json()["id"]},
                                    headers=g_headers)

    payload_checkin = {
        "cliente_id": resp_cli.json()["id"],
        "quarto_id": resp_quarto.json()["id"],
        "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
        "versao_quarto": resp_quarto.json()["versao"]
    }
    resp_hosp = await client.post("/hospedagens/checkin", json=payload_checkin, headers=r_headers)
    return resp_hosp.json()["id"]


@pytest.mark.asyncio
async def test_api_lancar_consumo_com_sucesso(client: AsyncClient, token_recepcionista: str, hospedagem_ativa_id):
    """Testa o registo de um produto na conta do quarto."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {
        "hospedagem_id": hospedagem_ativa_id,
        "descricao": "Menu Executivo",
        "quantidade": 2,
        "valor_unitario": 45.00
    }

    response = await client.post("/itens-consumo/", json=payload, headers=r_headers)

    assert response.status_code == 201
    dados = response.json()
    assert dados["descricao"] == "Menu Executivo"
    # O Pydantic deve devolver o subtotal calculado (2 * 45 = 90)
    assert float(dados["subtotal"]) == 90.00


@pytest.mark.asyncio
async def test_api_lancar_consumo_quantidade_invalida_retorna_422(client: AsyncClient, token_recepcionista: str, hospedagem_ativa_id):
    """O Pydantic deve travar quantidades zero ou negativas antes de chegar ao Domínio."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {
        "hospedagem_id": hospedagem_ativa_id,
        "descricao": "Água",
        "quantidade": 0,  # Inválido!
        "valor_unitario": 5.00
    }

    response = await client.post("/itens-consumo/", json=payload, headers=r_headers)
    assert response.status_code == 422  # Unprocessable Entity
    assert "quantidade" in response.text


@pytest.mark.asyncio
async def test_api_obter_extrato_de_consumos(client: AsyncClient, token_recepcionista: str, hospedagem_ativa_id):
    """Testa a rota GET que devolve a lista para a impressão da conta final."""
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    # Lança dois itens diferentes
    await client.post("/itens-consumo/", json={
        "hospedagem_id": hospedagem_ativa_id, "descricao": "Água", "quantidade": 1, "valor_unitario": 5.00
    }, headers=r_headers)
    await client.post("/itens-consumo/", json={
        "hospedagem_id": hospedagem_ativa_id, "descricao": "Vinho", "quantidade": 1, "valor_unitario": 120.00
    }, headers=r_headers)

    # Act: Busca o extrato
    response = await client.get(f"/itens-consumo/hospedagem/{hospedagem_ativa_id}", headers=r_headers)

    assert response.status_code == 200
    extrato = response.json()
    assert len(extrato) == 2
    assert extrato[0]["descricao"] == "Água"
    assert extrato[1]["descricao"] == "Vinho"
