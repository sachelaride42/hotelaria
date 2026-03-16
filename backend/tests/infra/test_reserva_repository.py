import pytest
from datetime import date
from backend.src.domain.models.reserva import Reserva
from backend.src.infra.repositories.reserva_repository import ReservaRepository


@pytest.mark.asyncio
async def test_contar_reservas_conflitantes(db_session):
    repo = ReservaRepository(db_session)

    # Reserva existente de 10 a 15 de Outubro
    await repo.salvar(
        Reserva(cliente_id=1, tipo_quarto_id=99, data_entrada=date(2026, 10, 10), data_saida=date(2026, 10, 15)))

    # Nova tentativa: 12 a 18 de Outubro (Cruza no meio!)
    conflitos = await repo.contar_reservas_conflitantes(99, date(2026, 10, 12), date(2026, 10, 18))
    assert conflitos == 1

    # Nova tentativa: 20 a 25 de Outubro (Totalmente fora, livre!)
    conflitos_livre = await repo.contar_reservas_conflitantes(99, date(2026, 10, 20), date(2026, 10, 25))
    assert conflitos_livre == 0