import pytest
from datetime import date
from backend.src.domain.models.reserva import Reserva
from backend.src.infra.repositories.reserva_repository import ReservaRepository


@pytest.mark.asyncio
async def test_atualizar_reserva(db_session):
    """salvar com id preenchido deve atualizar status, valor e datas da reserva."""
    from backend.src.domain.models.reserva import StatusReserva
    from decimal import Decimal
    repo = ReservaRepository(db_session)

    reserva = await repo.salvar(
        Reserva(cliente_id=1, tipo_quarto_id=1, data_entrada=date(2027, 1, 1), data_saida=date(2027, 1, 5))
    )

    reserva.data_entrada = date(2027, 2, 1)
    reserva.data_saida = date(2027, 2, 10)
    reserva.valor_total_previsto = Decimal("900.00")
    atualizado = await repo.salvar(reserva)

    assert atualizado.data_entrada == date(2027, 2, 1)
    assert atualizado.data_saida == date(2027, 2, 10)
    assert atualizado.valor_total_previsto == Decimal("900.00")

    buscado = await repo.buscar_por_id(reserva.id)
    assert buscado.data_entrada == date(2027, 2, 1)


@pytest.mark.asyncio
async def test_deletar_reserva(db_session):
    """deletar deve remover a reserva; buscar_por_id retorna None depois."""
    repo = ReservaRepository(db_session)
    reserva = await repo.salvar(
        Reserva(cliente_id=1, tipo_quarto_id=1, data_entrada=date(2027, 3, 1), data_saida=date(2027, 3, 5))
    )

    await repo.deletar(reserva.id)

    assert await repo.buscar_por_id(reserva.id) is None


@pytest.mark.asyncio
async def test_deletar_reserva_inexistente_nao_lanca_erro(db_session):
    repo = ReservaRepository(db_session)
    await repo.deletar(9999)


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