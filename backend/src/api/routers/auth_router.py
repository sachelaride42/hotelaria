from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.usuario_repository import UsuarioRepository
from backend.src.domain.services.auth_service import AuthService
from backend.src.api.schemas.token import TokenOutput

# O prefix "/auth" é definido no main.py ao registrar este router
router = APIRouter(tags=["Autenticação"])

def get_usuario_repo(session: AsyncSession = Depends(get_db_session)) -> UsuarioRepository:
    return UsuarioRepository(session)

@router.post("/login", response_model=TokenOutput)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """Valida as credenciais e retorna um token JWT de acesso."""
    usuario = await repo.buscar_por_email(form_data.username)

    if not usuario or not usuario.verificar_senha(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = {
        "sub": usuario.email,
        "role": usuario.tipo.value
    }
    access_token = AuthService.criar_token(token_payload)
    return {"access_token": access_token, "token_type": "bearer"}