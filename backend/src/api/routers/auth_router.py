from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.usuario_repository import UsuarioRepository
from backend.src.domain.services.auth_service import AuthService
from backend.src.api.schemas.token import TokenOutput

# Não colocamos prefix aqui porque geralmente a rota é apenas /auth/login, 
# e o prefixo "/auth" já foi definido lá no main.py
router = APIRouter(tags=["Autenticação"])

def get_usuario_repo(session: AsyncSession = Depends(get_db_session)) -> UsuarioRepository:
    return UsuarioRepository(session)

@router.post("/login", response_model=TokenOutput)
async def login(
    # O OAuth2PasswordRequestForm injeta 'username' e 'password' lidos como Form Data
    form_data: OAuth2PasswordRequestForm = Depends(),
    repo: UsuarioRepository = Depends(get_usuario_repo)
):
    """
    Endpoint de Autenticação.
    Recebe as credenciais, valida a hash da senha e devolve o JWT.
    """
    
    # 1. Busca o usuário na base de dados pelo e-mail (que o OAuth2 chama de username)
    usuario = await repo.buscar_por_email(form_data.username)
    
    # 2. Confere se o usuário existe e se a senha está correta
    # O método verificar_senha usa o bcrypt por baixo dos panos (Domínio)
    if not usuario or not usuario.verificar_senha(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Prepara os dados públicos (Payload) que vão dentro do Token
    token_payload = {
        "sub": usuario.email,           # Subject: quem é o dono do token
        "role": usuario.tipo.value      # Role: nível de permissão (GERENTE ou RECEPCIONISTA)
    }

    # 4. Assina o Token usando a nossa chave secreta (Serviço)
    access_token = AuthService.criar_token(token_payload)

    # 5. Devolve o token empacotado para o Frontend usar nos Headers das próximas requisições
    return {"access_token": access_token, "token_type": "bearer"}