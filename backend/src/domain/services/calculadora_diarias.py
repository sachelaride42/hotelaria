from datetime import datetime
from decimal import Decimal
import math


class CalculadoraDeDiarias:
    """""
    Serviço de Domínio puro.
    Aplica as políticas de cobrança do hotel sem depender de banco de dados.
    """

    HORARIO_PADRAO_CHECKOUT = 12  # 12:00 PM (Meio-dia)

    @staticmethod
    def calcular_total(
            data_checkin: datetime,
            data_checkout: datetime,
            valor_diaria: Decimal
    ) -> Decimal:

        if data_checkout <= data_checkin:
            raise ValueError("A data de checkout deve ser posterior ao check-in.")

        # 1. Calcula os dias inteiros baseados na virada de noite
        dias_estadia = (data_checkout.date() - data_checkin.date()).days

        # Se entrou e saiu no mesmo dia, cobra pelo menos 1 diária (Day Use)
        if dias_estadia == 0:
            return valor_diaria

        total = Decimal(dias_estadia) * valor_diaria

        # 2. Lógica de Check-out Flexível (Late Checkout)
        # Se o hóspede saiu no dia correto, mas DEPOIS do horário padrão (12h)
        if data_checkout.hour > CalculadoraDeDiarias.HORARIO_PADRAO_CHECKOUT:
            horas_extras = data_checkout.hour - CalculadoraDeDiarias.HORARIO_PADRAO_CHECKOUT

            # Aplicando a regra mencionada no TCC: "ex: 2 diárias + 1/4 diária até 15h"
            if horas_extras <= 3:  # Saiu até as 15h
                acrescimo = valor_diaria * Decimal('0.25')  # 1/4 da diária
            elif horas_extras <= 6:  # Saiu até as 18h
                acrescimo = valor_diaria * Decimal('0.50')  # Meia diária
            else:
                acrescimo = valor_diaria  # Mais que 18h, cobra diária cheia

            total += acrescimo

        # O retorno é arredondado para 2 casas decimais (formato moeda)
        return total.quantize(Decimal('0.00'))