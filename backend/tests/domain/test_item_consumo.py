import pytest
from decimal import Decimal
from backend.src.domain.models.item_consumo import ItemConsumo

def test_criar_consumo_calcula_subtotal_corretamente():
    item = ItemConsumo(
        hospedagem_id=1,
        descricao="Cerveja Artesanal",
        quantidade=3,
        valor_unitario=Decimal("15.50")
    )
    # 3 * 15.50 = 46.50
    assert item.subtotal == Decimal("46.50")

def test_impedir_consumo_com_quantidade_invalida():
    with pytest.raises(ValueError, match="maior que zero"):
        ItemConsumo(hospedagem_id=1, descricao="Água", quantidade=0, valor_unitario=Decimal("5.00"))

def test_impedir_consumo_com_valor_negativo():
    with pytest.raises(ValueError, match="não pode ser negativo"):
        ItemConsumo(hospedagem_id=1, descricao="Água", quantidade=1, valor_unitario=Decimal("-5.00"))