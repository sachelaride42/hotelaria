from datetime import datetime
from decimal import Decimal
import math


class CalculadoraDeDiarias:
    """Serviço de domínio que aplica as políticas de cobrança de diárias sem acesso ao banco."""

    HORARIO_PADRAO_CHECKOUT = 12  # 12:00 PM (Meio-dia)

    @staticmethod
    def calcular_total(
            data_checkin: datetime,
            data_checkout: datetime,
            valor_diaria: Decimal
    ) -> Decimal:

        if data_checkout <= data_checkin:
            raise ValueError("A data de checkout deve ser posterior ao check-in.")

        # Dias calculados pela virada de data (não pelas horas decorridas)
        dias_estadia = (data_checkout.date() - data_checkin.date()).days

        # Day Use: entrada e saída no mesmo dia cobram uma diária mínima
        if dias_estadia == 0:
            return valor_diaria

        total = Decimal(dias_estadia) * valor_diaria

        # Late checkout: acréscimo proporcional quando a saída ultrapassa o horário padrão
        if data_checkout.hour > CalculadoraDeDiarias.HORARIO_PADRAO_CHECKOUT:
            horas_extras = data_checkout.hour - CalculadoraDeDiarias.HORARIO_PADRAO_CHECKOUT

            if horas_extras <= 3:   # até 15h: 1/4 de diária
                acrescimo = valor_diaria * Decimal('0.25')
            elif horas_extras <= 6:  # até 18h: meia diária
                acrescimo = valor_diaria * Decimal('0.50')
            else:                    # após 18h: diária cheia
                acrescimo = valor_diaria

            total += acrescimo

        return total.quantize(Decimal('0.00'))