from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.usuario_repository import UsuarioRepository
from backend.src.domain.models.usuario import Usuario, TipoUsuario
from backend.src.domain.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_usuario_repo(session: AsyncSession = Depends(get_db_session)) -> UsuarioRepository:
    return UsuarioRepository(session)

async def get_usuario_logado(
    token: str = Depends(oauth2_scheme),
    repo: UsuarioRepository = Depends(get_usuario_repo)
) -> Usuario:
    """Decodifica o token JWT e retorna o usuário autenticado; lança 401 se inválido."""
    excecao = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = AuthService.verificar_token(token)
    
    if payload is None:
        raise excecao
        
    email: str = payload.get("sub")
    if not isinstance(email, str) or not email:
        raise excecao

    usuario = await repo.buscar_por_email(email)
    if usuario is None:
        raise excecao
        
    return usuario

async def exigir_gerente(usuario: Usuario = Depends(get_usuario_logado)) -> Usuario:
    """Verifica se o usuário autenticado possui o papel de Gerente; lança 403 caso contrário."""
    if usuario.tipo != TipoUsuario.GERENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso negado. Ação restrita a Gerentes."
        )
    return usuario