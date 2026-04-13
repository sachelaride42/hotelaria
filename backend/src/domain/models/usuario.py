from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import bcrypt 

class TipoUsuario(str, Enum):
    GERENTE = "GERENTE"
    RECEPCIONISTA = "RECEPCIONISTA"

@dataclass
class Usuario:
    nome: str
    email: str
    senha_hash: str
    tipo: TipoUsuario
    id: Optional[int] = None

    def verificar_senha(self, senha_plana: str) -> bool:
        """Verifica a senha usando bcrypt diretamente."""
        return bcrypt.checkpw(
            senha_plana.encode('utf-8'), 
            self.senha_hash.encode('utf-8')
        )

    @staticmethod
    def gerar_hash(senha_plana: str) -> str:
        """Gera o salt e o hash usando bcrypt nativo."""
        salt = bcrypt.gensalt()
        hash_bytes = bcrypt.hashpw(senha_plana.encode('utf-8'), salt)
        return hash_bytes.decode('utf-8')

@dataclass
class Gerente(Usuario):
    tipo: TipoUsuario = field(default=TipoUsuario.GERENTE, init=False)

@dataclass
class Recepcionista(Usuario):
    tipo: TipoUsuario = field(default=TipoUsuario.RECEPCIONISTA, init=False)