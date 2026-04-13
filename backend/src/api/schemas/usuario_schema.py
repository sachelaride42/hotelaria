from pydantic import BaseModel, ConfigDict, EmailStr, Field
from backend.src.domain.models.usuario import TipoUsuario

class UsuarioBase(BaseModel):
    """
    Atributos base compartilhados tanto na entrada (criação) 
    quanto na saída (leitura) dos dados.
    """
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


class UsuarioCriarInput(UsuarioBase):
    """
    Schema de Entrada (Input).
    É o ÚNICO momento em que o sistema lida com a senha.
    Ela entra em texto plano aqui, vai para o Domínio e vira hash antes de encostar no banco.
    """
    senha: str = Field(
        ..., 
        min_length=6, 
        description="Senha em texto plano (mínimo de 6 caracteres)."
    )


class UsuarioOutput(UsuarioBase):
    """
    Schema de Saída (Output) - O que o Frontend recebe.
    Prova de maturidade em segurança: A propriedade 'senha' foi intencionalmente 
    omitida deste schema. É impossível a API vazar a senha acidentalmente.
    """
    id: int

    model_config = ConfigDict(from_attributes=True)