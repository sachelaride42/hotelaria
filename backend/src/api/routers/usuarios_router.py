from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.usuario_repository import UsuarioRepository, EmailDuplicadoError
from backend.src.domain.models.usuario import Usuario, Gerente, Recepcionista, TipoUsuario
from backend.src.api.schemas.usuario_schema import UsuarioCriarInput, UsuarioOutput
from backend.src.api.dependencies.seguranca import exigir_gerente

router = APIRouter(
    prefix="/usuarios",
    tags=["Gestão de Usuários"],
    dependencies=[Depends(exigir_gerente)]
)

def get_usuario_repo(session: AsyncSession = Depends(get_db_session)) -> UsuarioRepository:
    return UsuarioRepository(session)

@router.post("/", response_model=UsuarioOutput, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    payload: UsuarioCriarInput,
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Cria um novo usuário administrativo (Gerente) ou operacional (Recepcionista)."""
    
    # 1. O Domínio cuida de gerar o hash com bcrypt
    senha_segura = Usuario.gerar_hash(payload.senha)
    
    # 2. Instancia a classe correta com base no payload
    if payload.tipo == TipoUsuario.GERENTE:
        novo_usuario = Gerente(nome=payload.nome, email=payload.email, senha_hash=senha_segura)
    elif payload.tipo == TipoUsuario.RECEPCIONISTA:
        novo_usuario = Recepcionista(nome=payload.nome, email=payload.email, senha_hash=senha_segura)
    else:
        raise HTTPException(status_code=400, detail="Tipo de usuário inválido.")

    # 3. Salva no banco (O repositório resolve o Single Table Inheritance)
    try:
        return await repo.salvar(novo_usuario)
    except EmailDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))