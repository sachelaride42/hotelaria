from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.produto_servico_repository import ProdutoServicoRepository, ProdutoDuplicadoError
from backend.src.domain.models.produto_servico import ProdutoServico
from backend.src.api.schemas.produto_servico_schema import ProdutoServicoBase, ProdutoServicoOutput

router = APIRouter(prefix="/catalogo", tags=["Catálogo de Produtos e Serviços"])

def get_catalogo_repo(session: AsyncSession = Depends(get_db_session)) -> ProdutoServicoRepository:
    return ProdutoServicoRepository(session)

@router.post("/", response_model=ProdutoServicoOutput, status_code=status.HTTP_201_CREATED)
async def criar_item_catalogo(
    payload: ProdutoServicoBase,
    repo: ProdutoServicoRepository = Depends(get_catalogo_repo)
):
    try:
        novo_item = ProdutoServico(**payload.model_dump())
        return await repo.salvar(novo_item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProdutoDuplicadoError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/", response_model=List[ProdutoServicoOutput])
async def listar_catalogo(repo: ProdutoServicoRepository = Depends(get_catalogo_repo)):
    return await repo.listar_todos()