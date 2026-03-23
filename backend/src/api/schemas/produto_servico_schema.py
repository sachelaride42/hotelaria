from pydantic import BaseModel, Field, condecimal, ConfigDict
from backend.src.domain.models.produto_servico import CategoriaItem
from backend.src.api.schemas.types import ValorMonetario

class ProdutoServicoBase(BaseModel):
    descricao: str = Field(..., min_length=2)
    preco_padrao: ValorMonetario
    categoria: CategoriaItem

class ProdutoServicoOutput(ProdutoServicoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)