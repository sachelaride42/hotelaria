from decimal import Decimal

import pytest
import pytest_asyncio

from backend.src.domain.models.quarto import Quarto, StatusQuarto
from backend.src.domain.models.tipo_quarto import TipoDeQuarto
from backend.src.infra.repositories.quarto_repository import QuartoRepository, ConcorrenciaQuartoError
from backend.src.infra.repositories.tipo_quarto_repository import TipoQuartoRepository

from backend.tests.conftest import TestingSessionLocal

@pytest_asyncio.fixture
async def tipo_quarto_padrao(db_session):
    """Fixture auxiliar para criar um tipo de quarto antes dos quartos."""
    repo = TipoQuartoRepository(db_session)
    tipo = TipoDeQuarto(nome="Casal", precoBaseDiaria=Decimal("150.00"), capacidade=2)
    return await repo.salvar(tipo)

@pytest.mark.asyncio
async def test_salvar_novo_quarto(db_session, tipo_quarto_padrao):
    repo = QuartoRepository(db_session)
    quarto = Quarto(numero="101", andar=1, tipo_quarto_id=tipo_quarto_padrao.id)

    quarto_salvo = await repo.salvar(quarto)

    assert quarto_salvo.id is not None
    assert quarto_salvo.versao == 1  # A versão inicial deve ser sempre 1 no banco



@pytest.mark.asyncio
async def test_atualizar_quarto_incrementa_versao(db_session, tipo_quarto_padrao):
    """Garante que o SQLAlchemy atualiza a versão automaticamente ao salvar."""
    repo = QuartoRepository(db_session)
    quarto = await repo.salvar(Quarto(numero="202", andar=2, tipo_quarto_id=tipo_quarto_padrao.id))

    # Simulando o check-in
    quarto.atualizarStatus(StatusQuarto.OCUPADO)
    quarto_atualizado = await repo.salvar(quarto)

    assert quarto_atualizado.status == StatusQuarto.OCUPADO
    assert quarto_atualizado.versao == 2  # O banco subiu para 2 automaticamente!


@pytest.mark.asyncio
async def test_optimistic_locking_impede_sobrescrita_simultanea(db_session, tipo_quarto_padrao):
    """
    Simula exatamente duas requisições web concorrentes.
    Cada requisição abre sua própria sessão com o banco de dados.
    """
    # 1. SETUP: Criamos o quarto usando a sessão padrão do teste
    repo_setup = QuartoRepository(db_session)
    quarto_original = await repo_setup.salvar(Quarto(numero="303", andar=3, tipo_quarto_id=tipo_quarto_padrao.id))

    # 2. SIMULAÇÃO DE CONCORRÊNCIA: Abrimos duas sessões (como se fossem dois navegadores)
    async with TestingSessionLocal() as sessao_A:
        async with TestingSessionLocal() as sessao_B:
            repo_A = QuartoRepository(sessao_A)
            repo_B = QuartoRepository(sessao_B)

            # Ambos lêem o quarto ao mesmo tempo (versão 1)
            quarto_A = await repo_A.buscar_por_id(quarto_original.id)
            quarto_B = await repo_B.buscar_por_id(quarto_original.id)

            # Recepcionista A altera o status e salva (Sucesso! Banco vai para versão 2)
            quarto_A.atualizarStatus(StatusQuarto.OCUPADO)
            await repo_A.salvar(quarto_A)

            # Recepcionista B tenta alterar (Ele ainda acha que a versão é 1)
            quarto_B.atualizarStatus(StatusQuarto.MANUTENCAO)

            # Boom! O SQLAlchemy intercepta a incompatibilidade de versão.
            with pytest.raises(ConcorrenciaQuartoError, match="modificado por outro usuário"):
                await repo_B.salvar(quarto_B)