import pytest
from decimal import Decimal
from backend.src.domain.models.tipo_quarto import TipoDeQuarto

def test_criar_tipo_quarto_valido():
    """Verifica a criação de um tipo de quarto com dados válidos."""
    tipo = TipoDeQuarto(nome="Casal", precoBaseDiaria=Decimal("150.00"), capacidade=2)
    assert tipo.precoBaseDiaria == Decimal("150.00")

def test_tipo_quarto_preco_invalido():
    """Impede a criação de tipo de quarto com preço não-positivo."""
    with pytest.raises(ValueError, match="maior que zero"):
        TipoDeQuarto(nome="Casal", precoBaseDiaria=Decimal("-10.00"), capacidade=2)