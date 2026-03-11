import pytest
from httpx import AsyncClient
from backend.src.domain.models.quarto import StatusQuarto


@pytest.mark.asyncio
async def test_api_criar_quarto(client: AsyncClient):
    payload = {"numero": "101", "andar": 1}
    response = await client.post("/quartos/", json=payload)

    assert response.status_code == 201
    dados = response.json()
    assert dados["numero"] == "101"
    assert dados["versao"] == 1
    assert dados["status"] == StatusQuarto.LIVRE.value


@pytest.mark.asyncio
async def test_api_atualizar_status_exige_versao(client: AsyncClient):
    """Testa a atualização de status e a trava de segurança da versão."""
    # 1. Cria o quarto
    await client.post("/quartos/", json={"numero": "202", "andar": 2})

    # 2. Atualiza o status enviando a versão correta (1)
    payload_atualizacao = {"status": StatusQuarto.SUJO.value, "versao": 1}
    response_patch = await client.patch("/quartos/1/status", json=payload_atualizacao)

    assert response_patch.status_code == 200
    assert response_patch.json()["status"] == StatusQuarto.SUJO.value
    assert response_patch.json()["versao"] == 2  # Versão subiu!


@pytest.mark.asyncio
async def test_api_atualizar_status_com_versao_velha_retorna_409(client: AsyncClient):
    """
    O Recepcionista envia uma versão desatualizada.
    A API deve rejeitar com HTTP 409 Conflict.
    """
    await client.post("/quartos/", json={"numero": "303", "andar": 3})

    # O quarto está na versão 1 no banco. O usuário manda versão 0 (desatualizada).
    payload_errado = {"status": StatusQuarto.OCUPADO.value, "versao": 0}
    response = await client.patch("/quartos/1/status", json=payload_errado)

    assert response.status_code == 409
    assert "atualizado por outro usuário" in response.json()["detail"]