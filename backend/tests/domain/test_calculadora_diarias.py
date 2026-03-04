import pytest
from datetime import datetime
from decimal import Decimal
from backend.src.domain.services.calculadora_diarias import CalculadoraDeDiarias


def test_calculo_diaria_padrao_sem_atraso():
    """Testa uma estadia de 2 dias com saída antes do meio-dia."""
    # Arrange
    checkin = datetime(2026, 3, 10, 14, 0)  # Entrou às 14h
    checkout = datetime(2026, 3, 12, 11, 0)  # Saiu às 11h (antes das 12h)
    valor = Decimal("200.00")

    # Act
    total = CalculadoraDeDiarias.calcular_total(checkin, checkout, valor)

    # Assert
    assert total == Decimal("400.00")  # 2 diárias exatas


def test_calculo_day_use():
    """Testa o cenário onde o hóspede entra e sai no mesmo dia."""
    checkin = datetime(2026, 3, 10, 8, 0)
    checkout = datetime(2026, 3, 10, 20, 0)
    valor = Decimal("200.00")

    total = CalculadoraDeDiarias.calcular_total(checkin, checkout, valor)
    assert total == Decimal("200.00")  # Cobra 1 diária mínima


def test_late_checkout_ate_15h():
    """Testa a regra do TCC: saída até 15h adiciona 1/4 da diária."""
    checkin = datetime(2026, 3, 10, 14, 0)
    checkout = datetime(2026, 3, 12, 14, 30)  # Saiu 14:30 (Atraso de < 3h do padrão 12h)
    valor = Decimal("200.00")

    total = CalculadoraDeDiarias.calcular_total(checkin, checkout, valor)

    # 2 diárias (400) + 1/4 de diária (50) = 450
    assert total == Decimal("450.00")


def test_erro_data_invertida():
    """Garante que o serviço bloqueia datas absurdas."""
    checkin = datetime(2026, 3, 12, 14, 0)
    checkout = datetime(2026, 3, 10, 12, 0)  # Checkout ANTES do check-in
    valor = Decimal("200.00")

    with pytest.raises(ValueError, match="posterior ao check-in"):
        CalculadoraDeDiarias.calcular_total(checkin, checkout, valor)