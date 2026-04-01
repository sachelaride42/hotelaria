import pytest
from decimal import Decimal
from backend.src.domain.models.produto_servico import ProdutoServico, CategoriaItem

def test_criar_produto_valido():
    """Testa a criação de um item físico (Produto)"""
    item = ProdutoServico(
        descricao="Refrigerante Lata",
        preco_padrao=Decimal("6.50"),
        categoria=CategoriaItem.PRODUTO
    )
    assert item.descricao == "Refrigerante Lata"
    assert item.categoria == CategoriaItem.PRODUTO

def test_criar_servico_valido():
    """Testa a criação de um serviço"""
    item = ProdutoServico(
        descricao="Taxa de Lavandaria",
        preco_padrao=Decimal("35.00"),
        categoria=CategoriaItem.SERVICO
    )
    assert item.categoria == CategoriaItem.SERVICO

def test_impedir_descricao_vazia():
    """Garante que não existem itens sem nome no catálogo"""
    with pytest.raises(ValueError, match="descrição do produto/serviço é obrigatória"):
        ProdutoServico(descricao="   ", preco_padrao=Decimal("10.00"), categoria=CategoriaItem.PRODUTO)

def test_impedir_preco_negativo():
    """O hotel não pode dever dinheiro ao cliente por consumir algo"""
    with pytest.raises(ValueError, match="preço padrão não pode ser negativo"):
        ProdutoServico(descricao="Água", preco_padrao=Decimal("-5.00"), categoria=CategoriaItem.PRODUTO)