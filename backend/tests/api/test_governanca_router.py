import pytest
import pytest_asyncio
from httpx import AsyncClient
from backend.src.domain.models.quarto import StatusLimpeza, StatusOcupacao


@pytest_asyncio.fixture
async def setup_quarto(client: AsyncClient, token_gerente: str):
    """Cria um tipo de quarto e um quarto via API, retorna o quarto criado."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp_tipo = await client.post("/tipos-quarto/", json={"nome": "Standard", "precoBaseDiaria": 100.00, "capacidade": 2}, headers=headers)
    tipo_id = resp_tipo.json()["id"]
    resp_quarto = await client.post("/quartos/", json={"numero": "101", "andar": 1, "tipo_quarto_id": tipo_id}, headers=headers)
    return resp_quarto.json()


@pytest.mark.asyncio
async def test_listar_quartos_para_limpeza_retorna_apenas_sujos(client: AsyncClient, token_gerente: str, setup_quarto: dict):
    """Somente quartos com status SUJO aparecem na lista de limpeza."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    quarto = setup_quarto

    # Sem marcar como sujo, a lista deve estar vazia
    resp = await client.get("/governanca/limpeza", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

    # Solicitar limpeza (LIMPO → SUJO)
    await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                       json={"versao": quarto["versao"]}, headers=headers)

    resp = await client.get("/governanca/limpeza", headers=headers)
    assert resp.status_code == 200
    dados = resp.json()
    assert len(dados) == 1
    assert dados[0]["id"] == quarto["id"]
    assert dados[0]["status_limpeza"] == StatusLimpeza.SUJO.value


@pytest.mark.asyncio
async def test_listar_quartos_sem_token_retorna_401(client: AsyncClient):
    resp = await client.get("/governanca/limpeza")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_solicitar_limpeza_com_sucesso(client: AsyncClient, token_gerente: str, setup_quarto: dict):
    """Solicitar limpeza de quarto LIMPO/LIVRE → retorna SUJO com versão incrementada."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    quarto = setup_quarto

    resp = await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                               json={"versao": quarto["versao"]}, headers=headers)

    assert resp.status_code == 200
    dados = resp.json()
    assert dados["status_limpeza"] == StatusLimpeza.SUJO.value
    assert dados["versao"] == quarto["versao"] + 1


@pytest.mark.asyncio
async def test_solicitar_limpeza_quarto_inexistente_retorna_404(client: AsyncClient, token_gerente: str):
    headers = {"Authorization": f"Bearer {token_gerente}"}
    resp = await client.patch("/governanca/limpeza/9999/solicitar", json={"versao": 1}, headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_solicitar_limpeza_quarto_ja_sujo_retorna_400(client: AsyncClient, token_gerente: str, setup_quarto: dict):
    """Solicitar limpeza de quarto que já é SUJO → 400."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    quarto = setup_quarto

    # Primeira solicitação
    await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                       json={"versao": quarto["versao"]}, headers=headers)

    # Segunda solicitação (já está SUJO)
    resp = await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                               json={"versao": quarto["versao"] + 1}, headers=headers)
    assert resp.status_code == 400
    assert "já está marcado para limpeza" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_solicitar_limpeza_versao_errada_retorna_409(client: AsyncClient, token_gerente: str, setup_quarto: dict):
    """Versão desatualizada → 409 Conflict."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    quarto = setup_quarto

    resp = await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                               json={"versao": 0}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_solicitar_limpeza_quarto_ocupado_permitido(client: AsyncClient, token_gerente: str, token_recepcionista: str, setup_quarto: dict):
    """Solicitar limpeza de quarto OCUPADO é permitido — ex.: quarto que acabou de ter checkout."""
    g_headers = {"Authorization": f"Bearer {token_gerente}"}
    r_headers = {"Authorization": f"Bearer {token_recepcionista}"}
    quarto = setup_quarto

    # Ocupar o quarto primeiro
    resp_ocupar = await client.patch(f"/quartos/{quarto['id']}/status-ocupacao",
                                     json={"status_ocupacao": StatusOcupacao.OCUPADO.value, "versao": quarto["versao"]},
                                     headers=r_headers)
    nova_versao = resp_ocupar.json()["versao"]

    resp = await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                               json={"versao": nova_versao}, headers=g_headers)
    assert resp.status_code == 200
    assert resp.json()["status_limpeza"] == StatusLimpeza.SUJO.value


@pytest.mark.asyncio
async def test_concluir_limpeza_com_sucesso(client: AsyncClient, token_gerente: str, setup_quarto: dict):
    """Concluir limpeza de quarto SUJO → retorna LIMPO com versão incrementada."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    quarto = setup_quarto

    # Primeiro marcar como SUJO
    resp_solicitar = await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                                        json={"versao": quarto["versao"]}, headers=headers)
    versao_sujo = resp_solicitar.json()["versao"]

    # Concluir limpeza
    resp = await client.patch(f"/governanca/limpeza/{quarto['id']}/concluir",
                               json={"versao": versao_sujo}, headers=headers)

    assert resp.status_code == 200
    dados = resp.json()
    assert dados["status_limpeza"] == StatusLimpeza.LIMPO.value
    assert dados["versao"] == versao_sujo + 1


@pytest.mark.asyncio
async def test_concluir_limpeza_quarto_limpo_retorna_400(client: AsyncClient, token_gerente: str, setup_quarto: dict):
    """Concluir limpeza de quarto que já é LIMPO → 400."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    quarto = setup_quarto  # nasce LIMPO

    resp = await client.patch(f"/governanca/limpeza/{quarto['id']}/concluir",
                               json={"versao": quarto["versao"]}, headers=headers)
    assert resp.status_code == 400
    assert "já está limpo" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_concluir_limpeza_versao_errada_retorna_409(client: AsyncClient, token_gerente: str, setup_quarto: dict):
    """Versão desatualizada na conclusão → 409 Conflict."""
    headers = {"Authorization": f"Bearer {token_gerente}"}
    quarto = setup_quarto

    # Marcar como SUJO
    await client.patch(f"/governanca/limpeza/{quarto['id']}/solicitar",
                       json={"versao": quarto["versao"]}, headers=headers)

    resp = await client.patch(f"/governanca/limpeza/{quarto['id']}/concluir",
                               json={"versao": 0}, headers=headers)
    assert resp.status_code == 409
