from datetime import time

class PoliticasHotel:
    """Centraliza as regras imutáveis (ou parâmetros) de negócio do hotel."""
    HORARIO_PADRAO_CHECKIN = time(14, 0)  # 14:00
    HORARIO_PADRAO_CHECKOUT = time(12, 0) # 12:00