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
async def test_impedir_descricao_duplicada(db_session):
    repo = ProdutoServicoRepository(db_session)

    item1 = ProdutoServico(descricao="Item Único", preco_padrao=Decimal("10.00"), categoria=CategoriaItem.PRODUTO)
    await repo.salvar(item1)

    item2 = ProdutoServico(descricao="Item Único", preco_padrao=Decimal("15.00"), categoria=CategoriaItem.SERVICO)

    # O PostgreSQL deve lançar IntegrityError, que o nosso Repositório converte para ProdutoDuplicadoError
    with pytest.raises(ProdutoDuplicadoError, match="Já existe um produto ou serviço com esta descrição"):
        await repo.salvar(item2)