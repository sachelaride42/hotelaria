from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.pagamento_repository import PagamentoRepository
from backend.src.infra.repositories.hospedagem_repository import HospedagemRepository
from backend.src.domain.models.hospedagem import StatusHospedagem
from backend.src.domain.models.pagamento import Pagamento
from backend.src.api.schemas.pagamento_schema import PagamentoInput, PagamentoOutput
from backend.src.api.dependencies.seguranca import get_usuario_logado, exigir_gerente

router = APIRouter(
    prefix="/pagamentos",
    tags=["Pagamentos"],
    dependencies=[Depends(get_usuario_logado)]
)


def get_pagamento_repo(session: AsyncSession = Depends(get_db_session)) -> PagamentoRepository:
    return PagamentoRepository(session)


def get_hospedagem_repo(session: AsyncSession = Depends(get_db_session)) -> HospedagemRepository:
    return HospedagemRepository(session)


@router.post("/", response_model=PagamentoOutput, status_code=status.HTTP_201_CREATED)
async def registrar_pagamento(
        payload: PagamentoInput,
        session: AsyncSession = Depends(get_db_session),
):
    """Registra um pagamento parcial ou total para uma hospedagem ativa."""
    hosp_repo = HospedagemRepository(session)
    pag_repo = PagamentoRepository(session)

    hospedagem = await hosp_repo.buscar_por_id(payload.hospedagem_id)
    if not hospedagem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospedagem não encontrada.")
    if hospedagem.status != StatusHospedagem.ATIVA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Só é possível registrar pagamentos em hospedagens ativas."
        )

    try:
        novo_pagamento = Pagamento(
            hospedagem_id=payload.hospedagem_id,
            valor_pago=payload.valor_pago,
            forma_pagamento=payload.forma_pagamento,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return await pag_repo.salvar(novo_pagamento)


@router.get("/hospedagem/{hospedagem_id}", response_model=List[PagamentoOutput])
async def listar_pagamentos(
        hospedagem_id: int,
        repo: PagamentoRepository = Depends(get_pagamento_repo),
):
    """Lista todos os pagamentos registrados para uma hospedagem."""
    return await repo.listar_por_hospedagem(hospedagem_id)


@router.delete("/{pagamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_pagamento(
        pagamento_id: int,
        session: AsyncSession = Depends(get_db_session),
):
    """Remove um pagamento. Exige GERENTE e hospedagem ainda ATIVA."""
    pag_repo = PagamentoRepository(session)
    hosp_repo = HospedagemRepository(session)

    pagamento = await pag_repo.buscar_por_id(pagamento_id)
    if not pagamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pagamento não encontrado.")

    hospedagem = await hosp_repo.buscar_por_id(pagamento.hospedagem_id)
    if hospedagem and hospedagem.status != StatusHospedagem.ATIVA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível remover pagamentos de uma hospedagem já finalizada."
        )

    await pag_repo.deletar(pagamento_id)
