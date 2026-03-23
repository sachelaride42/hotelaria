from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Importações do nosso projeto
from backend.src.infra.database import get_db_session  # (Você precisará criar esse gerador de sessão no database.py)
from backend.src.infra.repositories.quarto_repository import QuartoRepository, ConcorrenciaQuartoError
from backend.src.domain.models.quarto import Quarto
from backend.src.api.schemas.quarto_schema import QuartoCriarInput, QuartoAtualizarStatusInput, QuartoOutput

router = APIRouter(prefix="/quartos", tags=["Quartos"])


# Injeção de dependência: O FastAPI cuida de criar o repositório para nós
def get_quarto_repo(session: AsyncSession = Depends(get_db_session)) -> QuartoRepository:
    return QuartoRepository(session)


@router.post("/", response_model=QuartoOutput, status_code=status.HTTP_201_CREATED)
async def criar_quarto(
        payload: QuartoCriarInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """Cria um novo quarto no sistema."""
    novo_quarto = Quarto(numero=payload.numero, andar=payload.andar, tipo_quarto_id=payload.tipo_quarto_id)

    quarto_salvo = await repo.salvar(novo_quarto)
    return quarto_salvo


@router.patch("/{quarto_id}/status", response_model=QuartoOutput)
async def atualizar_status_quarto(
        quarto_id: int,
        payload: QuartoAtualizarStatusInput,
        repo: QuartoRepository = Depends(get_quarto_repo)
):
    """
    Atualiza o status do quarto.
    Exige o envio da 'versao' para prevenir a Condição de Corrida (Race Condition).
    """
    # 1. Busca o quarto no banco
    quarto = await repo.buscar_por_id(quarto_id)
    if not quarto:
        raise HTTPException(status_code=404, detail="Quarto não encontrado.")

    # 2. Segurança do Optimistic Locking (A API valida se o frontend está desatualizado)
    if quarto.versao != payload.versao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O quarto foi atualizado por outro usuário. Recarregue a página."
        )

    # 3. Executa a regra de negócio do Domínio (que foi testada exaustivamente!)
    try:
        quarto.atualizarStatus(payload.status)
    except ValueError as erro_dominio:
        # Pega a regra do "Quarto sujo não pode ir pra ocupado" e devolve HTTP 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro_dominio))

    # 4. Salva no banco (O repositório vai testar a versão lá no PostgreSQL novamente)
    try:
        quarto_salvo = await repo.salvar(quarto)
        return quarto_salvo
    except ConcorrenciaQuartoError as erro_banco:
        # Última barreira de defesa caso alguém salve no exato milissegundo de diferença
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