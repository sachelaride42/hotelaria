from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.usuario_repository import UsuarioRepository, EmailDuplicadoError
from backend.src.domain.models.usuario import Usuario, Gerente, Recepcionista, TipoUsuario
from backend.src.api.schemas.usuario_schema import UsuarioCriarInput, UsuarioAtualizarInput, UsuarioOutput
from backend.src.api.dependencies.seguranca import exigir_gerente

router = APIRouter(
    prefix="/usuarios",
    tags=["Gestão de Usuários"],
    dependencies=[Depends(exigir_gerente)]
)

def get_usuario_repo(session: AsyncSession = Depends(get_db_session)) -> UsuarioRepository:
    return UsuarioRepository(session)

@router.get("/", response_model=List[UsuarioOutput])
async def listar_usuarios(
    nome: Optional[str] = Query(None, description="Busca parcial pelo nome"),
    tipo: Optional[TipoUsuario] = Query(None, description="Filtrar por tipo (GERENTE ou RECEPCIONISTA)"),
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Lista todos os usuários do sistema."""
    return await repo.listar(nome=nome, tipo=tipo)


@router.get("/{usuario_id}", response_model=UsuarioOutput)
async def buscar_usuario(
    usuario_id: int,
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Retorna um usuário pelo ID."""
    usuario = await repo.buscar_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return usuario


@router.post("/", response_model=UsuarioOutput, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    payload: UsuarioCriarInput,
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Cria um novo usuário administrativo (Gerente) ou operacional (Recepcionista)."""
    
    senha_segura = Usuario.gerar_hash(payload.senha)

    if payload.tipo == TipoUsuario.GERENTE:
        novo_usuario = Gerente(nome=payload.nome, email=payload.email, senha_hash=senha_segura)
    elif payload.tipo == TipoUsuario.RECEPCIONISTA:
        novo_usuario = Recepcionista(nome=payload.nome, email=payload.email, senha_hash=senha_segura)
    else:
        raise HTTPException(status_code=400, detail="Tipo de usuário inválido.")

    try:
        return await repo.salvar(novo_usuario)
    except EmailDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/{usuario_id}", response_model=UsuarioOutput)
async def atualizar_usuario(
    usuario_id: int,
    payload: UsuarioAtualizarInput,
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Atualiza dados de um usuário existente. Se a senha for omitida, mantém a atual."""
    usuario_existente = await repo.buscar_por_id(usuario_id)
    if not usuario_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    senha_hash = Usuario.gerar_hash(payload.senha) if payload.senha else usuario_existente.senha_hash

    if payload.tipo == TipoUsuario.GERENTE:
        usuario_atualizado = Gerente(id=usuario_existente.id, nome=payload.nome, email=payload.email, senha_hash=senha_hash)
    else:
        usuario_atualizado = Recepcionista(id=usuario_existente.id, nome=payload.nome, email=payload.email, senha_hash=senha_hash)

    try:
        return await repo.salvar(usuario_atualizado)
    except EmailDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_usuario(
    usuario_id: int,
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Remove um usuário do sistema."""
    usuario = await repo.buscar_por_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    await repo.deletar(usuario_id)