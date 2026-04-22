import pytest
from decimal import Decimal

from backend.src.domain.models.pagamento import Pagamento, FormaDePagamento


def test_criar_pagamento_valido():
    """Um pagamento com dados corretos é criado sem erros."""
    pagamento = Pagamento(
        hospedagem_id=1,
        valor_pago=Decimal("150.00"),
        forma_pagamento=FormaDePagamento.PIX,
    )
    assert pagamento.hospedagem_id == 1
    assert pagamento.valor_pago == Decimal("150.00")
    assert pagamento.forma_pagamento == FormaDePagamento.PIX
    assert pagamento.id is None


def test_criar_pagamento_valor_zero_lanca_erro():
    """Valor zero deve levantar ValueError."""
    with pytest.raises(ValueError, match="maior que zero"):
        Pagamento(
            hospedagem_id=1,
            valor_pago=Decimal("0.00"),
            forma_pagamento=FormaDePagamento.DINHEIRO,
        )


def test_criar_pagamento_valor_negativo_lanca_erro():
    """Valor negativo deve levantar ValueError."""
    with pytest.raises(ValueError, match="maior que zero"):
        Pagamento(
            hospedagem_id=1,
            valor_pago=Decimal("-10.00"),
            forma_pagamento=FormaDePagamento.CARTAO_CREDITO,
        )


def test_forma_de_pagamento_enum_valores():
    """Verifica que todos os valores do Enum estão presentes."""
    formas = {f.value for f in FormaDePagamento}
    assert formas == {"DINHEIRO", "CARTAO_CREDITO", "CARTAO_DEBITO", "PIX", "BOLETO"}
