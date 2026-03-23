from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ClienteBase(BaseModel):
    """Atributos comuns para criação e atualização"""
    nome: str = Field(..., description="Nome completo do cliente")
    telefone: str = Field(..., description="Telefone de contato principal")
    cpf: Optional[str] = Field(None, description="CPF contendo 11 dígitos numéricos")
    email: Optional[str] = Field(None, description="E-mail do cliente")

class ClienteCriarInput(ClienteBase):
    """Payload recebido no POST /clientes"""
    pass

class ClienteAtualizarInput(ClienteBase):
    """Payload recebido no PUT /clientes"""
    pass

class ClienteOutput(ClienteBase):
    """Como devolvemos o cliente para o Frontend (React/Vue)"""
    id: int

    model_config = ConfigDict(from_attributes=True)  # Permite que o Pydantic leia a Dataclass do Domínio diretamente