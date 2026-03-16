import pytest
from decimal import Decimal
from backend.src.domain.models.tipo_quarto import TipoDeQuarto
from backend.src.domain.models.quarto import Quarto
from backend.src.infra.repositories.tipo_quarto_repository import TipoQuartoRepository
from backend.src.infra.repositories.quarto_repository import QuartoRepository


@pytest.mark.asyncio
async def test_salvar_e_buscar_tipo_quarto(db_session):
    repo = TipoQuartoRepository(db_session)
    tipo = TipoDeQuarto(nome="Simples", precoBaseDiaria=Decimal("100"), capacidade=1)
    salvo = await repo.salvar(tipo)
    assert salvo.id is not None


@pytest.mark.asyncio
async def test_contar_quartos_por_tipo(db_session):
    tipo_repo = TipoQuartoRepository(db_session)
    quarto_repo = QuartoRepository(db_session)

    # 1. Cria 2 Tipos de Quarto
    tipo1 = await tipo_repo.salvar(TipoDeQuarto(nome="T1", precoBaseDiaria=Decimal("100"), capacidade=1))
    tipo2 = await tipo_repo.salvar(TipoDeQuarto(nome="T2", precoBaseDiaria=Decimal("200"), capacidade=2))

    # 2. Cria 3 Quartos (dois do tipo 1, um do tipo 2)
    await quarto_repo.salvar(Quarto(numero="101", andar=1, tipo_quarto_id=tipo1.id))
    await quarto_repo.salvar(Quarto(numero="102", andar=1, tipo_quarto_id=tipo1.id))
    await quarto_repo.salvar(Quarto(numero="201", andar=2, tipo_quarto_id=tipo2.id))

    # 3. Act & Assert: Testa o novo método
    total_tipo_1 = await quarto_repo.contar_por_tipo(tipo1.id)
    total_tipo_2 = await quarto_repo.contar_por_tipo(tipo2.id)

    assert total_tipo_1 == 2
    assert total_tipo_2 == 1