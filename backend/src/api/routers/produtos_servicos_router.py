from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.produto_servico_repository import ProdutoServicoRepository, ProdutoDuplicadoError
from backend.src.domain.models.produto_servico import ProdutoServico
from backend.src.api.schemas.produto_servico_schema import ProdutoServicoBase, ProdutoServicoOutput
from backend.src.api.dependencies.seguranca import get_usuario_logado, exigir_gerente

router = APIRouter(
    prefix="/catalogo",
    tags=["Catálogo de Produtos e Serviços"],
    dependencies=[Depends(get_usuario_logado)]
)

def get_catalogo_repo(session: AsyncSession = Depends(get_db_session)) -> ProdutoServicoRepository:
    return ProdutoServicoRepository(session)

@router.post("/", response_model=ProdutoServicoOutput, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(exigir_gerente)])
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


@router.put("/{item_id}", response_model=ProdutoServicoOutput,
            dependencies=[Depends(exigir_gerente)])
async def atualizar_item_catalogo(
    item_id: int,
    payload: ProdutoServicoBase,
    repo: ProdutoServicoRepository = Depends(get_catalogo_repo)
):
    """Atualiza descrição, preço e categoria de um item do catálogo."""
    item = await repo.buscar_por_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item do catálogo não encontrado.")
    try:
        item.descricao = payload.descricao
        item.preco_padrao = payload.preco_padrao
        item.categoria = payload.categoria
        return await repo.salvar(item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProdutoDuplicadoError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(exigir_gerente)])
async def deletar_item_catalogo(
    item_id: int,
    repo: ProdutoServicoRepository = Depends(get_catalogo_repo)
):
    """Remove um item do catálogo de produtos e serviços."""
    item = await repo.buscar_por_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item do catálogo não encontrado.")
    await repo.deletar(item_id)