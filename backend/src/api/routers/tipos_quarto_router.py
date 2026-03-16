from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.tipo_quarto_repository import TipoQuartoRepository
from backend.src.domain.models.tipo_quarto import TipoDeQuarto
from backend.src.api.schemas.tipo_quarto_schema import TipoQuartoBase, TipoQuartoOutput

router = APIRouter(prefix="/tipos-quarto", tags=["Tipos de Quarto"])

def get_tipo_repo(session: AsyncSession = Depends(get_db_session)):
    return TipoQuartoRepository(session)

@router.post("/", response_model=TipoQuartoOutput, status_code=status.HTTP_201_CREATED)
async def criar_tipo_quarto(payload: TipoQuartoBase, repo: TipoQuartoRepository = Depends(get_tipo_repo)):
    novo_tipo = TipoDeQuarto(**payload.model_dump())
    return await repo.salvar(novo_tipo)