import pytest
import pytest_asyncio
from httpx import AsyncClient
from backend.src.domain.models.quarto import StatusOcupacao, StatusLimpeza


@pytest_asyncio.fixture
async def setup_tipo_quarto(client: AsyncClient, token_gerente: str):
    """Cria um tipo de quarto via API (gerente) e retorna o ID para os testes usarem."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {"nome": "Standard", "precoBaseDiaria": 100.00, "capacidade": 2}
    resp = await client.post("/tipos-quarto/", json=payload, headers=headers)
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_api_criar_quarto(client: AsyncClient, token_gerente: str, setup_tipo_quarto: int):
    """Gerente cria quarto com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload = {"numero": "101", "andar": 1, "tipo_quarto_id": setup_tipo_quarto}
    response = await client.post("/quartos/", json=payload, headers=headers)

    assert response.status_code == 201
    dados = response.json()
    assert dados["numero"] == "101"
    assert dados["versao"] == 1
    assert dados["status_ocupacao"] == StatusOcupacao.LIVRE.value
    assert dados["status_limpeza"] == StatusLimpeza.LIMPO.value


@pytest.mark.asyncio
async def test_api_criar_quarto_sem_token_retorna_401(client: AsyncClient, setup_tipo_quarto: int):
    """Criar quarto exige autenticação."""
    payload = {"numero": "999", "andar": 1, "tipo_quarto_id": setup_tipo_quarto}
    response = await client.post("/quartos/", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_criar_quarto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str, setup_tipo_quarto: int):
    """Apenas Gerentes podem criar quartos."""
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload = {"numero": "999", "andar": 1, "tipo_quarto_id": setup_tipo_quarto}
    response = await client.post("/quartos/", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_api_atualizar_status_limpeza_exige_versao(client: AsyncClient, token_gerente: str, token_recepcionista: str, setup_tipo_quarto: int):
    """Testa a atualização do status de limpeza e a trava de segurança da versão."""
    # 1. Gerente cria o quarto
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/quartos/", json={"numero": "202", "andar": 2, "tipo_quarto_id": setup_tipo_quarto}, headers=g_headers)
    quarto_id = resp.json()["id"]

    # 2. Recepcionista atualiza o status de limpeza com versão correta
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload_atualizacao = {"status_limpeza": StatusLimpeza.SUJO.value, "versao": 1}
    response_patch = await client.patch(f"/quartos/{quarto_id}/status-limpeza", json=payload_atualizacao, headers=r_headers)

    assert response_patch.status_code == 200
    assert response_patch.json()["status_limpeza"] == StatusLimpeza.SUJO.value
    assert response_patch.json()["versao"] == 2  # Versão subiu!


@pytest.mark.asyncio
async def test_api_atualizar_status_ocupacao_com_versao_velha_retorna_409(client: AsyncClient, token_gerente: str, setup_tipo_quarto: int):
    """Versão desatualizada retorna HTTP 409 Conflict."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/quartos/", json={"numero": "303", "andar": 3, "tipo_quarto_id": setup_tipo_quarto}, headers=g_headers)
    quarto_id = resp.json()["id"]

    # Versão 0 é desatualizada (quarto está na versão 1)
    payload_errado = {"status_ocupacao": StatusOcupacao.OCUPADO.value, "versao": 0}
    response = await client.patch(f"/quartos/{quarto_id}/status-ocupacao", json=payload_errado, headers=g_headers)

    assert response.status_code == 409
    assert "atualizado por outro usuário" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_atualizar_status_ocupacao_sujo_impede_ocupado(client: AsyncClient, token_gerente: str, token_recepcionista: str, setup_tipo_quarto: int):
    """Um quarto sujo não pode ser ocupado — a API deve retornar HTTP 400."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/quartos/", json={"numero": "404", "andar": 4, "tipo_quarto_id": setup_tipo_quarto}, headers=g_headers)
    quarto_id = resp.json()["id"]

    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    # Marca o quarto como sujo
    await client.patch(f"/quartos/{quarto_id}/status-limpeza", json={"status_limpeza": "SUJO", "versao": 1}, headers=r_headers)

    # Tenta ocupar o quarto sujo
    response = await client.patch(f"/quartos/{quarto_id}/status-ocupacao", json={"status_ocupacao": "OCUPADO", "versao": 2}, headers=r_headers)

    assert response.status_code == 400
    assert "limpo" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_atualizar_dados_quarto_sucesso(client: AsyncClient, token_gerente: str, setup_tipo_quarto: int):
    """Gerente atualiza os dados básicos de um quarto com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/quartos/", json={"numero": "501", "andar": 5, "tipo_quarto_id": setup_tipo_quarto}, headers=headers)
    quarto_id = resp.json()["id"]

    payload_update = {"numero": "502", "andar": 6, "tipo_quarto_id": setup_tipo_quarto}
    response = await client.put(f"/quartos/{quarto_id}", json=payload_update, headers=headers)

    assert response.status_code == 200
    assert response.json()["numero"] == "502"
    assert response.json()["andar"] == 6


@pytest.mark.asyncio
async def test_api_atualizar_dados_quarto_nao_encontrado(client: AsyncClient, token_gerente: str, setup_tipo_quarto: int):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    payload_update = {"numero": "999", "andar": 1, "tipo_quarto_id": setup_tipo_quarto}
    response = await client.put("/quartos/9999", json=payload_update, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_atualizar_dados_quarto_recepcionista_retorna_403(client: AsyncClient, token_recepcionista: str, setup_tipo_quarto: int):
    headers = {"Authorization": f"Bearer {token_recepcionista}"}
    payload_update = {"numero": "999", "andar": 1, "tipo_quarto_id": setup_tipo_quarto}
    response = await client.put("/quartos/1", json=payload_update, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_api_deletar_quarto_sucesso(client: AsyncClient, token_gerente: str, setup_tipo_quarto: int):
    """Gerente deleta um quarto livre com sucesso."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.post("/quartos/", json={"numero": "601", "andar": 6, "tipo_quarto_id": setup_tipo_quarto}, headers=headers)
    quarto_id = resp.json()["id"]

    response = await client.delete(f"/quartos/{quarto_id}", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_api_deletar_quarto_ocupado_retorna_400(client: AsyncClient, token_gerente: str, token_recepcionista: str, setup_tipo_quarto: int):
    """Não é possível deletar um quarto que está ocupado."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}

    resp_quarto = await client.post("/quartos/", json={"numero": "701", "andar": 7, "tipo_quarto_id": setup_tipo_quarto}, headers=g_headers)
    quarto_id = resp_quarto.json()["id"]
    versao = resp_quarto.json()["versao"]

    resp_cli = await client.post("/clientes/", json={"nome": "Hóspede", "telefone": "111"}, headers=r_headers)
    from datetime import datetime, timedelta
    checkin_payload = {
        "cliente_id": resp_cli.json()["id"],
        "quarto_id": quarto_id,
        "data_checkout_previsto": (datetime.now() + timedelta(days=2)).isoformat(),
        "versao_quarto": versao
    }
    await client.post("/hospedagens/checkin", json=checkin_payload, headers=r_headers)

    response = await client.delete(f"/quartos/{quarto_id}", headers=g_headers)
    assert response.status_code == 400
    assert "ocupado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_deletar_quarto_nao_encontrado(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    response = await client.delete("/quartos/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_deletar_quarto_sem_token_retorna_401(client: AsyncClient):
    response = await client.delete("/quartos/1")
    assert response.status_code == 401
