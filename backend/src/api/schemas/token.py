from pydantic import BaseModel

class TokenOutput(BaseModel):
    """Schema padrão exigido pelo protocolo OAuth2 para retorno de tokens."""
    access_token: str
    token_type: str

