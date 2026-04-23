from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ClienteBase(BaseModel):
    """Campos comuns a todos os schemas de cliente."""
    nome: str = Field(..., description="Nome completo do cliente")
    telefone: str = Field(..., description="Telefone de contato principal")
    cpf: Optional[str] = Field(None, description="CPF contendo 11 dígitos numéricos")
    email: Optional[str] = Field(None, description="E-mail do cliente")

class ClienteCriarInput(ClienteBase):
    """Schema de entrada para criação de cliente."""
    pass

class ClienteAtualizarInput(ClienteBase):
    """Schema de entrada para atualização de cliente."""
    pass

class ClienteOutput(ClienteBase):
    """Schema de saída para cliente."""
    id: int

    model_config = ConfigDict(from_attributes=True)