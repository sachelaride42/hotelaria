from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from decimal import Decimal
from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.tipo_quarto_repository import TipoQuartoRepository
from backend.src.infra.repositories.quarto_repository import QuartoRepository
from backend.src.domain.models.tipo_quarto import TipoDeQuarto
from backend.src.api.schemas.tipo_quarto_schema import TipoQuartoBase, TipoQuartoOutput
from backend.src.api.dependencies.seguranca import exigir_gerente, get_usuario_logado

router = APIRouter(
    prefix="/tipos-quarto",
    tags=["Tipos de Quarto"],
    dependencies=[Depends(get_usuario_logado)]
)

def get_tipo_repo(session: AsyncSession = Depends(get_db_session)):
    return TipoQuartoRepository(session)

def get_quarto_repo(session: AsyncSession = Depends(get_db_session)):
    return QuartoRepository(session)

@router.get("/", response_model=List[TipoQuartoOutput])
async def listar_tipos_quarto(
    capacidade_minima: Optional[int] = Query(None, description="Capacidade mínima de hóspedes"),
    preco_maximo: Optional[Decimal] = Query(None, description="Preço máximo da diária"),
    repo: TipoQuartoRepository = Depends(get_tipo_repo)
):
    """Lista todos os tipos de quarto cadastrados."""
    return await repo.listar(capacidade_minima=capacidade_minima, preco_maximo=preco_maximo)


@router.get("/{tipo_id}", response_model=TipoQuartoOutput)
async def buscar_tipo_quarto(
    tipo_id: int,
    repo: TipoQuartoRepository = Depends(get_tipo_repo)
):
    """Retorna um tipo de quarto pelo ID."""
    tipo = await repo.buscar_por_id(tipo_id)
    if not tipo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de quarto não encontrado.")
    return tipo


@router.post("/", response_model=TipoQuartoOutput, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(exigir_gerente)])
async def criar_tipo_quarto(payload: TipoQuartoBase, repo: TipoQuartoRepository = Depends(get_tipo_repo)):
    novo_tipo = TipoDeQuarto(**payload.model_dump())
    return await repo.salvar(novo_tipo)


@router.put("/{tipo_id}", response_model=TipoQuartoOutput,
            dependencies=[Depends(exigir_gerente)])
async def atualizar_tipo_quarto(
    tipo_id: int,
    payload: TipoQuartoBase,
    repo: TipoQuartoRepository = Depends(get_tipo_repo)
):
    """Atualiza nome, descrição, preço e capacidade de um tipo de quarto."""
    tipo_existente = await repo.buscar_por_id(tipo_id)
    if not tipo_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de quarto não encontrado.")
    tipo_existente.nome = payload.nome
    tipo_existente.descricao = payload.descricao
    tipo_existente.precoBaseDiaria = payload.precoBaseDiaria
    tipo_existente.capacidade = payload.capacidade
    return await repo.salvar(tipo_existente)


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(exigir_gerente)])
async def deletar_tipo_quarto(
    tipo_id: int,
    repo: TipoQuartoRepository = Depends(get_tipo_repo),
    quarto_repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Remove um tipo de quarto. Falha se houver quartos físicos vinculados a este tipo."""
    tipo = await repo.buscar_por_id(tipo_id)
    if not tipo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de quarto não encontrado.")

    total_quartos = await quarto_repo.contar_por_tipo(tipo_id)
    if total_quartos > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível remover este tipo pois há quartos físicos vinculados a ele."
        )
    await repo.deletar(tipo_id)