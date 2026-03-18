from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, session
from datetime import datetime

from backend.src.domain.services.calculadora_diarias import CalculadoraDeDiarias
from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.hospedagem_repository import HospedagemRepository
from backend.src.infra.repositories.quarto_repository import QuartoRepository, ConcorrenciaQuartoError
from backend.src.domain.models.hospedagem import Hospedagem
from backend.src.domain.models.quarto import StatusQuarto
from backend.src.api.schemas.hospedagem_schema import HospedagemCheckinInput, HospedagemOutput, HospedagemCheckoutInput
from backend.src.infra.repositories.reserva_repository import ReservaRepository
from backend.src.domain.models.reserva import StatusReserva
from backend.src.infra.repositories.tipo_quarto_repository import TipoQuartoRepository

router = APIRouter(prefix="/hospedagens", tags=["Hospedagens e Check-in"])


def get_hospedagem_repo(session: AsyncSession = Depends(get_db_session)) -> HospedagemRepository:
    return HospedagemRepository(session)


def get_quarto_repo(session: AsyncSession = Depends(get_db_session)) -> QuartoRepository:
    return QuartoRepository(session)


@router.post("/checkin", response_model=HospedagemOutput, status_code=status.HTTP_201_CREATED)
async def realizar_checkin(
        payload: HospedagemCheckinInput,
        session: AsyncSession = Depends(get_db_session),
):
    hosp_repo = HospedagemRepository(session)
    quarto_repo = QuartoRepository(session)
    reserva_repo = ReservaRepository(session)
    """
    UC3: Realizar Check-in.
    Cria a hospedagem e altera o estado do quarto para OCUPADO numa única transação.
    """
    # 1. Verifica se o Quarto existe e está LIVRE
    quarto = await quarto_repo.buscar_por_id(payload.quarto_id)
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")

    if quarto.status != StatusQuarto.LIVRE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O quarto {quarto.numero} não está livre. Estado atual: {quarto.status.value}."
        )

    # 2. Verifica a versão para o Optimistic Locking
    if quarto.versao != payload.versao_quarto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O quarto foi atualizado por outro recepcionista. Recarregue a página."
        )

    # NOVO: Validação e Atualização da Reserva (se existir)
    reserva_existente = None
    if payload.reserva_id:
        reserva_existente = await reserva_repo.buscar_por_id(payload.reserva_id)
        if not reserva_existente:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")
        if reserva_existente.status != StatusReserva.CONFIRMADA:
            raise HTTPException(status_code=400,
                                detail="Esta reserva não está Confirmada e não pode ser usada para check-in.")

        # Muda o status no domínio
        reserva_existente.status = StatusReserva.UTILIZADA

    # 3. Cria a Hospedagem (Domínio)
    try:
        nova_hospedagem = Hospedagem(
            cliente_id=payload.cliente_id,
            quarto_id=payload.quarto_id,
            reserva_id=payload.reserva_id,
            data_checkout_previsto=payload.data_checkout_previsto
        )
    except ValueError as erro_dominio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro_dominio))

    # 4. Atualiza o estado do Quarto
    quarto.atualizarStatus(StatusQuarto.OCUPADO)

    # 5. Persiste tudo na base de dados
    try:
        # Idealmente, gerido por um Unit of Work para garantir atomicidade total,
        # mas como partilhamos a mesma sessão (`session`), o commit final garante a segurança.
        hospedagem_salva = await hosp_repo.salvar(nova_hospedagem)
        await quarto_repo.salvar(quarto)
        if reserva_existente:
            await reserva_repo.salvar(reserva_existente)  # <-- RESERVA ATUALIZADA NO BANCO

        return hospedagem_salva
    except ConcorrenciaQuartoError as erro_banco:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro_banco))


@router.post("/{hospedagem_id}/checkout", response_model=HospedagemOutput)
async def realizar_checkout(
        hospedagem_id: int,
        payload: HospedagemCheckoutInput,
        session: AsyncSession = Depends(get_db_session),
):
    """
    UC5: Realizar Check-out.
    Calcula as diárias flexíveis, soma o consumo, finaliza a hospedagem e suja o quarto.
    """
    hosp_repo = HospedagemRepository(session)
    quarto_repo = QuartoRepository(session)
    tipo_quarto_repo = TipoQuartoRepository(session)
    consumo_repo = ItemConsumoRepository(session)
    # 1. Busca e valida a Hospedagem
    hospedagem = await hosp_repo.buscar_por_id(hospedagem_id)
    if not hospedagem:
        raise HTTPException(status_code=404, detail="Hospedagem não encontrada.")
    if hospedagem.status != "ATIVA":
        raise HTTPException(status_code=400, detail="Esta hospedagem já foi finalizada ou cancelada.")

    # 2. Busca o Quarto e valida a versão (Optimistic Locking)
    quarto = await quarto_repo.buscar_por_id(hospedagem.quarto_id)
    if quarto.versao != payload.versao_quarto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O quarto foi atualizado por outro usuário. Recarregue a página."
        )

    # 3. Busca o Preço da Diária no Tipo de Quarto
    tipo_quarto = await tipo_quarto_repo.buscar_por_id(quarto.tipo_quarto_id)

    # 4. A MATEMÁTICA: Diárias + Consumo
    data_saida_real = datetime.now()

    valor_diarias = CalculadoraDeDiarias.calcular_total(
        data_checkin=hospedagem.data_checkin,
        data_checkout=data_saida_real,
        valor_diaria=tipo_quarto.precoBaseDiaria
    )

    # Busca a soma de tudo que ele pegou no frigobar/restaurante
    total_consumo = await consumo_repo.somar_total_por_hospedagem(hospedagem_id)

    # O Grande Total a ser cobrado no cartão do cliente
    valor_final = valor_diarias + total_consumo

    # 5. Executa as Regras de Negócio nas Entidades (Domínio)
    try:
        hospedagem.realizar_checkout(data_saida=data_saida_real, valor_calculado=valor_final)
        quarto.atualizarStatus(StatusQuarto.SUJO)
    except ValueError as erro_dominio:
        raise HTTPException(status_code=400, detail=str(erro_dominio))

    # 6. Salva tudo no banco de dados na mesma transação
    try:
        hospedagem_salva = await hosp_repo.salvar(hospedagem)
        await quarto_repo.salvar(quarto)

        return hospedagem_salva

    except ConcorrenciaQuartoError as erro_banco:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro_banco))