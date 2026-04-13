from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

class AuthService:
    @staticmethod
    def criar_token(dados: dict) -> str:
        """Gerar token"""
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        dados.update({"exp": expira})
        return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verificar_token(token: str) -> Optional[dict]:
        """Verificar token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None