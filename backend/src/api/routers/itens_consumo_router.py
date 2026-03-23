from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.item_consumo_repository import ItemConsumoRepository
from backend.src.infra.repositories.hospedagem_repository import HospedagemRepository
from backend.src.domain.models.item_consumo import ItemConsumo
from backend.src.api.schemas.item_consumo_schema import ItemConsumoCriarInput, ItemConsumoOutput

router = APIRouter(prefix="/itens-consumo", tags=["Lançamentos de Consumo"])


def get_consumo_repo(session: AsyncSession = Depends(get_db_session)) -> ItemConsumoRepository:
    return ItemConsumoRepository(session)


def get_hospedagem_repo(session: AsyncSession = Depends(get_db_session)) -> HospedagemRepository:
    return HospedagemRepository(session)


@router.post("/", response_model=ItemConsumoOutput, status_code=status.HTTP_201_CREATED)
async def registar_consumo(
        payload: ItemConsumoCriarInput,
        session: AsyncSession = Depends(get_db_session),
):
    """Adiciona um item à conta do hóspede."""
    # Valida se a hospedagem existe e ainda está a decorrer
    repo = ItemConsumoRepository(session)
    hosp_repo = HospedagemRepository(session)
    hospedagem = await hosp_repo.buscar_por_id(payload.hospedagem_id)
    if not hospedagem:
        raise HTTPException(status_code=404, detail="Hospedagem não encontrada.")

    if hospedagem.status != "ATIVA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível adicionar consumo a uma conta finalizada."
        )

    try:
        novo_item = ItemConsumo(
            hospedagem_id=payload.hospedagem_id,
            descricao=payload.descricao,
            quantidade=payload.quantidade,
            valor_unitario=payload.valor_unitario
        )
        return await repo.salvar(novo_item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hospedagem/{hospedagem_id}", response_model=List[ItemConsumoOutput])
async def listar_extrato_consumo(
        hospedagem_id: int,
        repo: ItemConsumoRepository = Depends(get_consumo_repo)
):
    """Devolve todos os itens consumidos (o Extrato da Conta)."""
    return await repo.buscar_por_hospedagem(hospedagem_id)