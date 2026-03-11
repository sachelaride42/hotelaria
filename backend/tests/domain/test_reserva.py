import pytest
from datetime import date, timedelta
from decimal import Decimal
from backend.src.domain.models.reserva import Reserva, StatusReserva


def test_criar_reserva_valida():
    """Garante a criação bem-sucedida de uma reserva"""
    hoje = date.today()
    amanha = hoje + timedelta(days=1)

    reserva = Reserva(
        cliente_id=1,
        tipo_quarto_id=2,  # Ex: Suíte
        data_entrada=hoje,
        data_saida=amanha,
        valor_total_previsto=Decimal("350.00")
    )

    assert reserva.cliente_id == 1
    assert reserva.status == StatusReserva.CONFIRMADA
    assert reserva.data_entrada == hoje


def test_excecao_e2_data_saida_anterior_a_entrada():
    """Valida a Exceção E2 do TCC: A data de saída não pode ser antes da entrada"""
    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    with pytest.raises(ValueError, match="não pode ser anterior ou igual à data de entrada"):
        Reserva(
            cliente_id=1,
            tipo_quarto_id=1,
            data_entrada=hoje,
            data_saida=ontem,  # Data inválida!
            valor_total_previsto=Decimal("100.00")
        )


def test_excecao_e2_data_saida_igual_a_entrada():
    """Reserva de 0 dias não é permitida. Para Day Use, seria entrada de manhã e saída à noite do mesmo dia, mas na lógica de pernoite a data de saída é o dia seguinte"""
    hoje = date.today()

    with pytest.raises(ValueError, match="não pode ser anterior ou igual"):
        Reserva(cliente_id=1, tipo_quarto_id=1, data_entrada=hoje, data_saida=hoje)


def test_cancelar_reserva_sucesso():
    """Uma reserva confirmada pode ser cancelada"""
    reserva = Reserva(cliente_id=1, tipo_quarto_id=1, data_entrada=date(2026, 1, 1), data_saida=date(2026, 1, 5))
    reserva.cancelar()
    assert reserva.status == StatusReserva.CANCELADA


def test_impedir_cancelar_reserva_utilizada():
    """Uma reserva que já virou check-in (UTILIZADA) não pode ser cancelada"""
    reserva = Reserva(cliente_id=1, tipo_quarto_id=1, data_entrada=date(2026, 1, 1), data_saida=date(2026, 1, 5))
    reserva.status = StatusReserva.UTILIZADA

    with pytest.raises(ValueError, match="já realizou check-in"):
        reserva.cancelar()