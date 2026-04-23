from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.src.domain.models.usuario import TipoUsuario

class UsuarioBase(BaseModel):
    """Campos comuns a todos os schemas de usuário."""
    nome: str = Field(
        ..., 
        min_length=3, 
        max_length=150, 
        description="Nome completo do funcionário."
    )
    email: EmailStr = Field(
        ..., 
        description="E-mail corporativo que será usado no login."
    )
    tipo: TipoUsuario = Field(
        ..., 
        description="Nível de privilégio no sistema (GERENTE ou RECEPCIONISTA)."
    )


class UsuarioAtualizarInput(UsuarioBase):
    """Schema para atualizar um usuário. A senha é opcional — se omitida, mantém a atual."""
    senha: Optional[str] = Field(None, min_length=6, description="Nova senha (opcional).")


class UsuarioCriarInput(UsuarioBase):
    """Schema de entrada para criação de usuário; recebe a senha em texto plano."""
    senha: str = Field(
        ..., 
        min_length=6, 
        description="Senha em texto plano (mínimo de 6 caracteres)."
    )


class UsuarioOutput(UsuarioBase):
    """Schema de saída de usuário; omite a senha por segurança."""
    id: int

    model_config = ConfigDict(from_attributes=True)