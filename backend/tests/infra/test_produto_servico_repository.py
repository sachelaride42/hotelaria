import pytest
from decimal import Decimal
from backend.src.domain.models.produto_servico import ProdutoServico, CategoriaItem
from backend.src.infra.repositories.produto_servico_repository import ProdutoServicoRepository, ProdutoDuplicadoError


@pytest.mark.asyncio
async def test_salvar_e_buscar_produto(db_session):
    repo = ProdutoServicoRepository(db_session)
    item = ProdutoServico(descricao="Cerveja", preco_padrao=Decimal("12.00"), categoria=CategoriaItem.PRODUTO)

    salvo = await repo.salvar(item)
    buscado = await repo.buscar_por_id(salvo.id)

    assert buscado is not None
    assert buscado.descricao == "Cerveja"


@pytest.mark.asyncio
async def test_listar_todos_ordenados_por_descricao(db_session):
    repo = ProdutoServicoRepository(db_session)

    # Inserimos fora de ordem propositadamente
    await repo.salvar(
        ProdutoServico(descricao="Z - Último", preco_padrao=Decimal("1"), categoria=CategoriaItem.PRODUTO))
    await repo.salvar(
        ProdutoServico(descricao="A - Primeiro", preco_padrao=Decimal("1"), categoria=CategoriaItem.PRODUTO))
    await repo.salvar(ProdutoServico(descricao="M - Meio", preco_padrao=Decimal("1"), categoria=CategoriaItem.PRODUTO))

    lista = await repo.listar_todos()

    assert len(lista) == 3
    assert lista[0].descricao == "A - Primeiro"
    assert lista[1].descricao == "M - Meio"
    assert lista[2].descricao == "Z - Último"


@pytest.mark.asyncio
async def test_atualizar_produto_servico(db_session):
    """salvar com id preenchido deve atualizar descricao, preco e categoria."""
    repo = ProdutoServicoRepository(db_session)
    item = await repo.salvar(ProdutoServico(descricao="Massagem Relaxante", preco_padrao=Decimal("100.00"), categoria=CategoriaItem.SERVICO))

    item.descricao = "Massagem Terapêutica"
    item.preco_padrao = Decimal("130.00")
    atualizado = await repo.salvar(item)

    assert atualizado.descricao == "Massagem Terapêutica"
    assert atualizado.preco_padrao == Decimal("130.00")

    buscado = await repo.buscar_por_id(item.id)
    assert buscado.descricao == "Massagem Terapêutica"


@pytest.mark.asyncio
async def test_deletar_produto_servico(db_session):
    """deletar deve remover o item; buscar_por_id retorna None depois."""
    repo = ProdutoServicoRepository(db_session)
    item = await repo.salvar(ProdutoServico(descricao="Vitamina C", preco_padrao=Decimal("15.00"), categoria=CategoriaItem.PRODUTO))

    await repo.deletar(item.id)

    assert await repo.buscar_por_id(item.id) is None


@pytest.mark.asyncio
async def test_deletar_produto_inexistente_nao_lanca_erro(db_session):
    repo = ProdutoServicoRepository(db_session)
    await repo.deletar(9999)


@pytest.mark.asyncio
async def test_impedir_descricao_duplicada(db_session):
    repo = ProdutoServicoRepository(db_session)

    item1 = ProdutoServico(descricao="Item Único", preco_padrao=Decimal("10.00"), categoria=CategoriaItem.PRODUTO)
    await repo.salvar(item1)

    item2 = ProdutoServico(descricao="Item Único", preco_padrao=Decimal("15.00"), categoria=CategoriaItem.SERVICO)

    # O PostgreSQL deve lançar IntegrityError, que o nosso Repositório converte para ProdutoDuplicadoError
    with pytest.raises(ProdutoDuplicadoError, match="Já existe um produto ou serviço com esta descrição"):
        await repo.salvar(item2)