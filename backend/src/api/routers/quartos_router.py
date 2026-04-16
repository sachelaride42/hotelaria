from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Importações do nosso projeto
from backend.src.infra.database import get_db_session  # (Você precisará criar esse gerador de sessão no database.py)
from backend.src.infra.repositories.quarto_repository import QuartoRepository, ConcorrenciaQuartoError
from backend.src.domain.models.quarto import Quarto
from backend.src.api.schemas.quarto_schema import (
    QuartoCriarInput,
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