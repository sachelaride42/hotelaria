from datetime import date


class ServicoDisponibilidade:
    """
    Serviço que orquestra a verificação de disponibilidade (UC2).
    """

    @staticmethod
    def verificar_disponibilidade_tipo(
            tipo_quarto_id: int,
            data_entrada: date,
            data_saida: date,
            total_quartos_fisicos_deste_tipo: int,
            reservas_conflitantes: int
    ) -> bool:
        """
        Calcula se o hotel pode aceitar mais uma reserva para este tipo de quarto.
        """
        # Se não há quartos físicos desse tipo construídos no hotel
        if total_quartos_fisicos_deste_tipo <= 0:
            return False

        # Quartos livres = Total Físico - Reservas que cruzam com essa data
        quartos_livres = total_quartos_fisicos_deste_tipo - reservas_conflitantes

        # Se sobrar pelo menos 1, está disponível
        return quartos_livres > 0