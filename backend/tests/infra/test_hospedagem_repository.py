import pytest
from datetime import datetime, timedelta
from decimal import Decimal

import pytest_asyncio

from backend.src.domain.models.cliente import Cliente
from backend.src.domain.models.tipo_quarto import TipoDeQuarto
from backend.src.domain.models.quarto import Quarto
from backend.src.domain.models.hospedagem import Hospedagem, StatusHospedagem
from backend.src.infra.repositories.cliente_repository import ClienteRepository
from backend.src.infra.repositories.tipo_quarto_repository import TipoQuartoRepository
from backend.src.infra.repositories.quarto_repository import QuartoRepository
from backend.src.infra.repositories.hospedagem_repository import HospedagemRepository


@pytest_asyncio.fixture
async def setup_dependencias_hospedagem(db_session):
    """Cria os registos pais necessários (Cliente, TipoQuarto e Quarto)"""
    cliente = await ClienteRepository(db_session).salvar(Cliente(nome="João", telefone="123"))
    tipo = await TipoQuartoRepository(db_session).salvar(
        TipoDeQuarto(nome="Casal", precoBaseDiaria=Decimal("100"), capacidade=2))
    quarto = await QuartoRepository(db_session).salvar(Quarto(numero="101", andar=1, tipo_quarto_id=tipo.id))

    return {"cliente_id": cliente.id, "quarto_id": quarto.id}


@pytest.mark.asyncio
async def test_salvar_e_buscar_hospedagem(db_session, setup_dependencias_hospedagem):
    repo = HospedagemRepository(db_session)
    dados = setup_dependencias_hospedagem

    futuro = datetime.now() + timedelta(days=2)
    hospedagem = Hospedagem(cliente_id=dados["cliente_id"], quarto_id=dados["quarto_id"], data_checkout_previsto=futuro)

    # Act
    salva = await repo.salvar(hospedagem)
    buscada = await repo.buscar_por_id(salva.id)

    # Assert
    assert buscada is not None
    assert buscada.status == StatusHospedagem.ATIVA


@pytest.mark.asyncio
async def test_buscar_hospedagem_ativa_por_quarto(db_session, setup_dependencias_hospedagem):
    repo = HospedagemRepository(db_session)
    dados = setup_dependencias_hospedagem

    # 1. Cria a hospedagem ativa
    hospedagem = Hospedagem(
        cliente_id=dados["cliente_id"],
        quarto_id=dados["quarto_id"],
        data_checkout_previsto=datetime.now() + timedelta(days=1)
    )
    salva = await repo.salvar(hospedagem)

    # 2. Testa se o método encontra a ativa
    encontrada = await repo.buscar_ativa_por_quarto(dados["quarto_id"])
    assert encontrada is not None
    assert encontrada.id == salva.id

    # 3. Finaliza a hospedagem (Check-out)
    salva.realizar_checkout(data_saida=datetime.now(), valor_calculado=Decimal("100.00"))
    await repo.salvar(salva)

    # 4. Testa se o método ignora hospedagens finalizadas
    nao_encontrada = await repo.buscar_ativa_por_quarto(dados["quarto_id"])
    assert nao_encontrada is None