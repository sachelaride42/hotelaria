from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.quarto_repository import QuartoRepository, ConcorrenciaQuartoError
from backend.src.domain.models.quarto import Quarto, StatusOcupacao, StatusLimpeza
from backend.src.api.schemas.quarto_schema import (
    QuartoCriarInput,
    QuartoAtualizarDadosInput,
    QuartoAtualizarStatusOcupacaoInput,
    QuartoAtualizarStatusLimpezaInput,
    QuartoOutput,
)
from backend.src.api.dependencies.seguranca import get_usuario_logado, exigir_gerente

router = APIRouter(
    prefix="/quartos",
    tags=["Quartos"],
    dependencies=[Depends(get_usuario_logado)]
)


# Injeção de dependência: O FastAPI cuida de criar o repositório para nós
def get_quarto_repo(session: AsyncSession = Depends(get_db_session)) -> QuartoRepository:
    return QuartoRepository(session)


@router.get("/", response_model=List[QuartoOutput])
async def listar_quartos(
    status_ocupacao: Optional[StatusOcupacao] = Query(None, description="Filtrar por status de ocupação"),
    status_limpeza: Optional[StatusLimpeza] = Query(None, description="Filtrar por status de limpeza"),
    andar: Optional[int] = Query(None, description="Filtrar por andar"),
    tipo_quarto_id: Optional[int] = Query(None, description="Filtrar por tipo de quarto"),
    repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Lista todos os quartos com filtros opcionais."""
    return await repo.listar_todos(
        status_ocupacao=status_ocupacao,
        status_limpeza=status_limpeza,
        andar=andar,
        tipo_quarto_id=tipo_quarto_id,
    )


@router.post("/", response_model=QuartoOutput, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(exigir_gerente)])
async def criar_quarto(
        payload: QuartoCriarInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Cria um novo quarto no sistema."""
    novo_quarto = Quarto(numero=payload.numero, andar=payload.andar, tipo_quarto_id=payload.tipo_quarto_id)

    quarto_salvo = await repo.salvar(novo_quarto)
    return quarto_salvo


@router.patch("/{quarto_id}/status-ocupacao", response_model=QuartoOutput)
async def atualizar_status_ocupacao(
        quarto_id: int,
        payload: QuartoAtualizarStatusOcupacaoInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Atualiza o status de ocupação do quarto (LIVRE/OCUPADO/MANUTENCAO)."""
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")

    if quarto.versao != payload.versao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O quarto foi atualizado por outro usuário. Recarregue a página."
        )

    try:
        quarto.atualizarStatusOcupacao(payload.status_ocupacao)
    except ValueError as erro_dominio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro_dominio))

    try:
        quarto_salvo = await repo.salvar(quarto)
        return quarto_salvo
    except ConcorrenciaQuartoError as erro_banco:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro_banco))


@router.patch("/{quarto_id}/status-limpeza", response_model=QuartoOutput)
async def atualizar_status_limpeza(
        quarto_id: int,
        payload: QuartoAtualizarStatusLimpezaInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Atualiza o status de limpeza do quarto (LIMPO/SUJO)."""
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")

    if quarto.versao != payload.versao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O quarto foi atualizado por outro usuário. Recarregue a página."
        )

    try:
        quarto.atualizarStatusLimpeza(payload.status_limpeza)
    except ValueError as erro_dominio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro_dominio))

    try:
        quarto_salvo = await repo.salvar(quarto)
        return quarto_salvo
    except ConcorrenciaQuartoError as erro_banco:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro_banco))

@router.get("/{quarto_id}", response_model=QuartoOutput)
async def buscar_quarto(
        quarto_id: int,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")
    return quarto


@router.put("/{quarto_id}", response_model=QuartoOutput,
            dependencies=[Depends(exigir_gerente)])
async def atualizar_dados_quarto(
        quarto_id: int,
        payload: QuartoAtualizarDadosInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Atualiza número, andar e tipo de um quarto. Não afeta status nem versão."""
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")
    quarto_atualizado = await repo.atualizar_dados_basicos(
        quarto_id, payload.numero, payload.andar, payload.tipo_quarto_id
    )
    return quarto_atualizado


@router.delete("/{quarto_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(exigir_gerente)])
async def deletar_quarto(
        quarto_id: int,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Remove um quarto do sistema. Não é permitido deletar quartos ocupados."""
    from backend.src.domain.models.quarto import StatusOcupacao
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")
    if quarto.status_ocupacao == StatusOcupacao.OCUPADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível remover um quarto que está ocupado."
        )
    try:
        await repo.deletar(quarto_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir este quarto pois existem registros de hospedagem associados a ele."
        )