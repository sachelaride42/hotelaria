from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, time
from backend.src.domain.config_hotel import PoliticasHotel

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.reserva_repository import ReservaRepository
from backend.src.domain.models.reserva import Reserva
from backend.src.api.schemas.reserva_schema import ReservaCriarInput, ReservaOutput
from backend.src.domain.services.calculadora_diarias import CalculadoraDeDiarias

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def get_reserva_repo(session: AsyncSession = Depends(get_db_session)) -> ReservaRepository:
    return ReservaRepository(session)

@router.post("/", response_model=ReservaOutput, status_code=status.HTTP_201_CREATED)
async def criar_reserva(
        payload: ReservaCriarInput,
        repo: ReservaRepository = Depends(get_reserva_repo),
        # Precisamos do repositório de Tipos de Quarto para pegar o preço!
        tipo_quarto_repo: TipoQuartoRepository = Depends(get_tipo_quarto_repo)
):
    try:
        # 1. Busca o valor da diária no banco de dados com base no tipo solicitado
        tipo_quarto = await tipo_quarto_repo.buscar_por_id(payload.tipo_quarto_id)
        if not tipo_quarto:
            raise HTTPException(status_code=404, detail="Tipo de quarto não encontrado.")

        # 2. Simula os horários padrão de check-in e check-out do hotel (14h e 12h)
        # O Pydantic deu 'date', mas a calculadora precisa de 'datetime'.
        dt_entrada = datetime.combine(payload.data_entrada, PoliticasHotel.HORARIO_PADRAO_CHECKIN)
        dt_saida = datetime.combine(payload.data_saida, PoliticasHotel.HORARIO_PADRAO_CHECKOUT)

        # 3. Usa o NOSSO SERVIÇO para fazer a matemática com segurança
        valor_calculado = CalculadoraDeDiarias.calcular_total(
            data_checkin=dt_entrada,
            data_checkout=dt_saida,
            valor_diaria=tipo_quarto.precoBaseDiaria  # O valor seguro que veio do banco!
        )

        # 4. Agora sim, cria a reserva com o valor auditado pelo Backend
        nova_reserva = Reserva(
            cliente_id=payload.cliente_id,
            tipo_quarto_id=payload.tipo_quarto_id,
            data_entrada=payload.data_entrada,
            data_saida=payload.data_saida,
            valor_total_previsto=valor_calculado  # Injetado automaticamente
        )

        reserva_salva = await repo.salvar(nova_reserva)
        return reserva_salva

    except ValueError as erro_dominio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro_dominio))

@router.patch("/{reserva_id}/cancelar", response_model=ReservaOutput)
async def cancelar_reserva(
        reserva_id: int,
        repo: ReservaRepository = Depends(get_reserva_repo)
):
    """Cancela uma reserva existente, caso ainda não tenha sido utilizada."""
    reserva = await repo.buscar_por_id(reserva_id)
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")

    try:
        reserva.cancelar()
        reserva_salva = await repo.salvar(reserva)
        return reserva_salva
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))