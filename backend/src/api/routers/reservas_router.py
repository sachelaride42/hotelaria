from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, time

from backend.src.api.routers.quartos_router import get_quarto_repo
from backend.src.domain.config_hotel import PoliticasHotel
from backend.src.domain.services.servico_disponibilidade import ServicoDisponibilidade

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.quarto_repository import QuartoRepository
from backend.src.infra.repositories.reserva_repository import ReservaRepository
from backend.src.domain.models.reserva import Reserva
from backend.src.api.schemas.reserva_schema import ReservaCriarInput, ReservaOutput
from backend.src.domain.services.calculadora_diarias import CalculadoraDeDiarias
from backend.src.infra.repositories.tipo_quarto_repository import TipoQuartoRepository

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def get_reserva_repo(session: AsyncSession = Depends(get_db_session)) -> ReservaRepository:
    return ReservaRepository(session)

@router.post("/", response_model=ReservaOutput, status_code=status.HTTP_201_CREATED)
async def criar_reserva(
        payload: ReservaCriarInput,
        repo: ReservaRepository = Depends(get_reserva_repo),
        tipo_quarto_repo: TipoQuartoRepository = Depends(get_tipo_quarto_repo),
        quarto_repo: QuartoRepository = Depends(get_quarto_repo)  # ← NOVO
):
    try:
        # 1. Busca o tipo de quarto (valida existência e obtém o preço)
        tipo_quarto = await tipo_quarto_repo.buscar_por_id(payload.tipo_quarto_id)
        if not tipo_quarto:
            raise HTTPException(status_code=404, detail="Tipo de quarto não encontrado.")

        # 2. Verifica disponibilidade antes de qualquer cálculo financeiro
        total_quartos_fisicos = await quarto_repo.contar_por_tipo(payload.tipo_quarto_id)
        reservas_conflitantes = await repo.contar_reservas_conflitantes(
            payload.tipo_quarto_id, payload.data_entrada, payload.data_saida
        )
        disponivel = ServicoDisponibilidade.verificar_disponibilidade_tipo(
            tipo_quarto_id=payload.tipo_quarto_id,
            data_entrada=payload.data_entrada,
            data_saida=payload.data_saida,
            total_quartos_fisicos_deste_tipo=total_quartos_fisicos,
            reservas_conflitantes=reservas_conflitantes
        )
        if not disponivel:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não há quartos disponíveis para o período selecionado."
            )

        # 3. Simula os horários padrão de check-in e check-out do hotel (14h e 12h)
        dt_entrada = datetime.combine(payload.data_entrada, PoliticasHotel.HORARIO_PADRAO_CHECKIN)
        dt_saida = datetime.combine(payload.data_saida, PoliticasHotel.HORARIO_PADRAO_CHECKOUT)

        # 4. Usa o serviço de domínio para calcular o valor com segurança
        valor_calculado = CalculadoraDeDiarias.calcular_total(
            data_checkin=dt_entrada,
            data_checkout=dt_saida,
            valor_diaria=tipo_quarto.precoBaseDiaria
        )

        # 5. Cria a reserva com o valor auditado pelo backend
        nova_reserva = Reserva(
            cliente_id=payload.cliente_id,
            tipo_quarto_id=payload.tipo_quarto_id,
            data_entrada=payload.data_entrada,
            data_saida=payload.data_saida,
            valor_total_previsto=valor_calculado
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