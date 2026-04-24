import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from backend.src.domain.models.hospedagem import Hospedagem, StatusHospedagem


def test_criar_hospedagem_inicia_ativa():
    """Verifica que uma hospedagem recém-criada inicia com status ATIVA e valor zero."""
    futuro = datetime.now() + timedelta(days=2)
    hospedagem = Hospedagem(cliente_id=1, quarto_id=1, data_checkout_previsto=futuro)

    assert hospedagem.status == StatusHospedagem.ATIVA
    assert hospedagem.valor_total == Decimal("0.00")


def test_realizar_checkout_altera_status_e_valor():
    """Verifica que o check-out altera o status para FINALIZADA e registra a data e valor."""
    hospedagem = Hospedagem(cliente_id=1, quarto_id=1, data_checkout_previsto=datetime.now() + timedelta(days=1))

    data_saida = datetime.now() + timedelta(hours=5)
    valor_cobrado = Decimal("250.00")

    hospedagem.realizar_checkout(data_saida=data_saida, valor_calculado=valor_cobrado)

    assert hospedagem.status == StatusHospedagem.FINALIZADA
    assert hospedagem.data_checkout_real == data_saida
    assert hospedagem.valor_total == valor_cobrado


def test_criar_hospedagem_com_valor_negociado():
    """Hospedagem criada com preço negociado armazena o campo corretamente."""
    futuro = datetime.now() + timedelta(days=2)
    hospedagem = Hospedagem(
        cliente_id=1,
        quarto_id=1,
        data_checkout_previsto=futuro,
        valor_diaria_negociado=Decimal("150.00"),
    )

    assert hospedagem.valor_diaria_negociado == Decimal("150.00")


def test_impedir_checkout_duplicado():
    """Impede a realização de check-out em hospedagem já finalizada."""
    hospedagem = Hospedagem(cliente_id=1, quarto_id=1, data_checkout_previsto=datetime.now() + timedelta(days=1))
    hospedagem.realizar_checkout(data_saida=datetime.now() + timedelta(hours=1), valor_calculado=Decimal("100.00"))

    with pytest.raises(ValueError, match="Não é possível fazer check-out"):
        hospedagem.realizar_checkout(data_saida=datetime.now() + timedelta(hours=2), valor_calculado=Decimal("100.00"))