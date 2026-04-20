from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.quarto_repository import QuartoRepository, ConcorrenciaQuartoError
from backend.src.domain.models.quarto import StatusLimpeza
from backend.src.domain.services.servico_governanca import ServicoGovernanca
from backend.src.api.schemas.governanca_schema import SolicitarLimpezaInput, ConcluirLimpezaInput
from backend.src.api.schemas.quarto_schema import QuartoOutput
from backend.src.api.dependencies.seguranca import get_usuario_logado

router = APIRouter(
    prefix="/governanca",
    tags=["Governança"],
    dependencies=[Depends(get_usuario_logado)]
)


def get_quarto_repo(session: AsyncSession = Depends(get_db_session)) -> QuartoRepository:
    return QuartoRepository(session)


@router.get("/limpeza", response_model=list[QuartoOutput])
async def listar_quartos_para_limpeza(repo: QuartoRepository = Depends(get_quarto_repo)):
    """Retorna todos os quartos que necessitam de limpeza (status SUJO)."""
    todos = await repo.listar_todos()
    return ServicoGovernanca.filtrar_quartos_para_limpeza(todos)


@router.patch("/limpeza/{quarto_id}/solicitar", response_model=QuartoOutput)
async def solicitar_limpeza(
        quarto_id: int,
        payload: SolicitarLimpezaInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Registra que um quarto precisa de limpeza (LIMPO → SUJO)."""
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quarto não encontrado.")

    if quarto.versao != payload.versao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O quarto foi atualizado por outro usuário. Recarregue a página."
        )

    try:
        ServicoGovernanca.validar_solicitacao_limpeza(quarto)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro))

    quarto.atualizarStatusLimpeza(StatusLimpeza.SUJO)

    try:
        return await repo.salvar(quarto)
    except ConcorrenciaQuartoError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))


@router.patch("/limpeza/{quarto_id}/concluir", response_model=QuartoOutput)
async def concluir_limpeza(
        quarto_id: int,
        payload: ConcluirLimpezaInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Registra a conclusão da limpeza de um quarto (SUJO → LIMPO)."""
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quarto não encontrado.")

    if quarto.versao != payload.versao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O quarto foi atualizado por outro usuário. Recarregue a página."
        )

    try:
        ServicoGovernanca.validar_conclusao_limpeza(quarto)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro))

    quarto.atualizarStatusLimpeza(StatusLimpeza.LIMPO)

    try:
        return await repo.salvar(quarto)
    except ConcorrenciaQuartoError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))
