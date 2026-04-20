import pytest
from decimal import Decimal
from backend.src.domain.models.item_consumo import ItemConsumo
from backend.src.infra.repositories.item_consumo_repository import ItemConsumoRepository


@pytest.mark.asyncio
async def test_buscar_item_consumo_por_id(db_session):
    """buscar_por_id deve retornar o item correto e None para ids inexistentes."""
    repo = ItemConsumoRepository(db_session)
    salvo = await repo.salvar(ItemConsumo(hospedagem_id=1, descricao="Café", quantidade=1, valor_unitario=Decimal("5.00")))

    encontrado = await repo.buscar_por_id(salvo.id)
    assert encontrado is not None
    assert encontrado.descricao == "Café"

    nao_existe = await repo.buscar_por_id(9999)
    assert nao_existe is None


@pytest.mark.asyncio
async def test_atualizar_item_consumo(db_session):
    """salvar com id preenchido deve atualizar descricao, quantidade e valor_unitario."""
    repo = ItemConsumoRepository(db_session)
    item = await repo.salvar(ItemConsumo(hospedagem_id=1, descricao="Suco", quantidade=1, valor_unitario=Decimal("8.00")))

    item.descricao = "Suco de Manga"
    item.quantidade = 3
    item.valor_unitario = Decimal("10.00")
    atualizado = await repo.salvar(item)

    assert atualizado.descricao == "Suco de Manga"
    assert atualizado.quantidade == 3
    assert atualizado.valor_unitario == Decimal("10.00")
    assert atualizado.subtotal == Decimal("30.00")

    buscado = await repo.buscar_por_id(item.id)
    assert buscado.descricao == "Suco de Manga"


@pytest.mark.asyncio
async def test_deletar_item_consumo(db_session):
    """deletar deve remover o item; buscar_por_id retorna None depois."""
    repo = ItemConsumoRepository(db_session)
    item = await repo.salvar(ItemConsumo(hospedagem_id=1, descricao="Cerveja", quantidade=2, valor_unitario=Decimal("7.00")))

    await repo.deletar(item.id)

    assert await repo.buscar_por_id(item.id) is None


@pytest.mark.asyncio
async def test_deletar_item_inexistente_nao_lanca_erro(db_session):
    repo = ItemConsumoRepository(db_session)
    await repo.deletar(9999)


@pytest.mark.asyncio
async def test_somar_total_consumo_por_hospedagem(db_session):
    repo = ItemConsumoRepository(db_session)

    # Inserindo 3 consumos para a Hospedagem ID = 99
    await repo.salvar(
        ItemConsumo(hospedagem_id=99, descricao="Água", quantidade=2, valor_unitario=Decimal("5.00")))  # 10.00
    await repo.salvar(
        ItemConsumo(hospedagem_id=99, descricao="Lanche", quantidade=1, valor_unitario=Decimal("35.00")))  # 35.00
    await repo.salvar(
        ItemConsumo(hospedagem_id=99, descricao="Refrigerante", quantidade=1, valor_unitario=Decimal("8.00")))  # 8.00

    # Inserindo consumo para OUTRA hospedagem (não deve somar)
    await repo.salvar(ItemConsumo(hospedagem_id=100, descricao="Vinho", quantidade=1, valor_unitario=Decimal("100.00")))

    # Act: Somando apenas da hospedagem 99
    total = await repo.somar_total_por_hospedagem(99)

    # Assert: 10 + 35 + 8 = 53.00
    assert total == Decimal("53.00")
