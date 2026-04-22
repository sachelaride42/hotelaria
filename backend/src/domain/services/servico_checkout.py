from decimal import Decimal


class ServicoCheckout:
    """Serviço de domínio puro que encapsula a regra de pagamento no checkout."""

    @staticmethod
    def validar_pagamento_suficiente(valor_total: Decimal, total_pago: Decimal) -> None:
        """Garante que o hóspede pagou o suficiente antes de liberar o quarto."""
        if total_pago < valor_total:
            restante = valor_total - total_pago
            raise ValueError(
                f"Pagamento insuficiente. Total cobrado: R${valor_total:.2f}, "
                f"Pago: R${total_pago:.2f}, Restante: R${restante:.2f}."
            )
