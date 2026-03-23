import pytest
from decimal import Decimal
from backend.src.domain.models.item_consumo import ItemConsumo
from backend.src.infra.repositories.item_consumo_repository import ItemConsumoRepository


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
