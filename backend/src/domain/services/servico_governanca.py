from backend.src.domain.models.quarto import Quarto, StatusLimpeza


class ServicoGovernanca:
    """
    Serviço de domínio que encapsula as regras de negócio da Governança (Limpeza).
    """

    @staticmethod
    def filtrar_quartos_para_limpeza(quartos: list[Quarto]) -> list[Quarto]:
        """Retorna apenas os quartos com StatusLimpeza.SUJO."""
        return [q for q in quartos if q.status_limpeza == StatusLimpeza.SUJO]

    @staticmethod
    def validar_solicitacao_limpeza(quarto: Quarto) -> None:
        """Regra: não se pode solicitar limpeza de quarto que já está marcado como SUJO."""
        if quarto.status_limpeza == StatusLimpeza.SUJO:
            raise ValueError(f"O quarto {quarto.numero} já está marcado para limpeza.")

    @staticmethod
    def validar_conclusao_limpeza(quarto: Quarto) -> None:
        """Regra: só se pode concluir limpeza de um quarto SUJO."""
        if quarto.status_limpeza == StatusLimpeza.LIMPO:
            raise ValueError(f"O quarto {quarto.numero} já está limpo.")
