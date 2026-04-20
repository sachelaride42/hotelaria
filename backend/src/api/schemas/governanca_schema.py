from pydantic import BaseModel, Field


class SolicitarLimpezaInput(BaseModel):
    versao: int = Field(..., description="Versão atual do quarto para Optimistic Locking.")


class ConcluirLimpezaInput(BaseModel):
    versao: int = Field(..., description="Versão atual do quarto para Optimistic Locking.")
