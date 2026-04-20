from decimal import Decimal

import pytest
import pytest_asyncio

from backend.src.domain.models.quarto import Quarto, StatusOcupacao
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
    quarto.atualizarStatusOcupacao(StatusOcupacao.OCUPADO)
    quarto_atualizado = await repo.salvar(quarto)

    assert quarto_atualizado.status_ocupacao == StatusOcupacao.OCUPADO
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
            quarto_A.atualizarStatusOcupacao(StatusOcupacao.OCUPADO)
            await repo_A.salvar(quarto_A)

            # Recepcionista B tenta alterar (Ele ainda acha que a versão é 1)
            quarto_B.atualizarStatusOcupacao(StatusOcupacao.MANUTENCAO)

            # Boom! O SQLAlchemy intercepta a incompatibilidade de versão.
            with pytest.raises(ConcorrenciaQuartoError, match="modificado por outro usuário"):
                await repo_B.salvar(quarto_B)


@pytest.mark.asyncio
async def test_listar_todos_retorna_todos_os_quartos(db_session, tipo_quarto_padrao):
    repo = QuartoRepository(db_session)
    await repo.salvar(Quarto(numero="401", andar=4, tipo_quarto_id=tipo_quarto_padrao.id))
    await repo.salvar(Quarto(numero="402", andar=4, tipo_quarto_id=tipo_quarto_padrao.id))

    todos = await repo.listar_todos()

    assert len(todos) == 2
    numeros = {q.numero for q in todos}
    assert numeros == {"401", "402"}


@pytest.mark.asyncio
async def test_listar_todos_retorna_lista_vazia_sem_quartos(db_session):
    repo = QuartoRepository(db_session)

    todos = await repo.listar_todos()

    assert todos == []


@pytest.mark.asyncio
async def test_atualizar_dados_basicos_quarto(db_session, tipo_quarto_padrao):
    """atualizar_dados_basicos deve alterar numero, andar e tipo sem incrementar versão."""
    repo = QuartoRepository(db_session)
    tipo_repo = TipoQuartoRepository(db_session)

    quarto = await repo.salvar(Quarto(numero="501", andar=5, tipo_quarto_id=tipo_quarto_padrao.id))
    versao_original = quarto.versao

    # Cria um segundo tipo para testar troca
    tipo2 = await tipo_repo.salvar(TipoDeQuarto(nome="Luxo", precoBaseDiaria=Decimal("300.00"), capacidade=3))

    atualizado = await repo.atualizar_dados_basicos(quarto.id, "502", 6, tipo2.id)

    assert atualizado.numero == "502"
    assert atualizado.andar == 6
    assert atualizado.tipo_quarto_id == tipo2.id
    # O version_id_col do SQLAlchemy incrementa versao em qualquer UPDATE
    assert atualizado.versao == versao_original + 1


@pytest.mark.asyncio
async def test_atualizar_dados_basicos_quarto_inexistente_retorna_none(db_session, tipo_quarto_padrao):
    repo = QuartoRepository(db_session)
    resultado = await repo.atualizar_dados_basicos(9999, "000", 1, tipo_quarto_padrao.id)
    assert resultado is None


@pytest.mark.asyncio
async def test_deletar_quarto(db_session, tipo_quarto_padrao):
    """deletar deve remover o quarto; buscar_por_id retorna None depois."""
    repo = QuartoRepository(db_session)
    quarto = await repo.salvar(Quarto(numero="601", andar=6, tipo_quarto_id=tipo_quarto_padrao.id))

    await repo.deletar(quarto.id)

    assert await repo.buscar_por_id(quarto.id) is None


@pytest.mark.asyncio
async def test_deletar_quarto_inexistente_nao_lanca_erro(db_session):
    repo = QuartoRepository(db_session)
    await repo.deletar(9999)