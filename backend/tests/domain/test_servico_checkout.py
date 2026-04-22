import pytest
from decimal import Decimal

from backend.src.domain.services.servico_checkout import ServicoCheckout


def test_pagamento_exato_nao_lanca_erro():
    """Total pago igual ao total cobrado deve passar sem exceção."""
    ServicoCheckout.validar_pagamento_suficiente(
        valor_total=Decimal("420.00"),
        total_pago=Decimal("420.00"),
    )


def test_pagamento_acima_nao_lanca_erro():
    """Total pago maior que o cobrado (troco) deve passar sem exceção."""
    ServicoCheckout.validar_pagamento_suficiente(
        valor_total=Decimal("420.00"),
        total_pago=Decimal("500.00"),
    )


def test_pagamento_insuficiente_lanca_erro():
    """Total pago menor que o cobrado deve levantar ValueError."""
    with pytest.raises(ValueError, match="Pagamento insuficiente"):
        ServicoCheckout.validar_pagamento_suficiente(
            valor_total=Decimal("420.00"),
            total_pago=Decimal("20.00"),
        )


def test_mensagem_de_erro_contem_restante():
    """A mensagem de erro deve informar o valor restante corretamente."""
    with pytest.raises(ValueError) as exc_info:
        ServicoCheckout.validar_pagamento_suficiente(
            valor_total=Decimal("420.00"),
            total_pago=Decimal("20.00"),
        )
    assert "400.00" in str(exc_info.value)


def test_sem_nenhum_pagamento_lanca_erro():
    """Com zero pago, o serviço também deve barrar o checkout."""
    with pytest.raises(ValueError, match="Pagamento insuficiente"):
        ServicoCheckout.validar_pagamento_suficiente(
            valor_total=Decimal("200.00"),
            total_pago=Decimal("0.00"),
        )
