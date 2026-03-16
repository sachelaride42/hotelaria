import pytest
from backend.src.domain.models.quarto import Quarto, StatusQuarto


def test_criar_quarto_com_valores_padrao():
    #Garante que um quarto novo nasce livre e na versão 1
    # Arrange & Act
    quarto = Quarto(numero="101", andar=1, tipo_quarto_id=1)

    # Assert
    assert quarto.numero == "101"
    assert quarto.andar == 1
    assert quarto.status == StatusQuarto.LIVRE
    assert quarto.tipo_quarto_id == 1
    assert quarto.versao == 1
    assert quarto.id is None

def test_atualizar_status_transicao_valida():
    """Testa a mudança normal de estado do quarto"""
    # Arrange
    quarto = Quarto(numero="202", andar=2, tipo_quarto_id=2)
    assert quarto.status == StatusQuarto.LIVRE

    # Act
    quarto.atualizarStatus(StatusQuarto.OCUPADO)

    # Assert
    assert quarto.status == StatusQuarto.OCUPADO


def test_atualizar_status_impede_transicao_sujo_para_ocupado():
    #Testa a regra de negócio que impede alocar um hóspede em um quarto sujo.
    #O Pytest verifica se a exceção correta foi lançada.

    # Arrange
    quarto = Quarto(numero="303", andar=3, status=StatusQuarto.SUJO, tipo_quarto_id=3)

    # Act & Assert
    with pytest.raises(ValueError, match="Quarto precisa ser limpo antes de ser ocupado"):
        quarto.atualizarStatus(StatusQuarto.OCUPADO)


def test_atualizar_status_impede_transicao_manutencao_para_ocupado():
    # Garante que quartos em manutenção não sejam alocados no check-in
    # Arrange
    quarto = Quarto(numero="404", andar=4, status=StatusQuarto.MANUTENCAO, tipo_quarto_id=1)

    # Act & Assert
    with pytest.raises(ValueError, match=f"O quarto {quarto.numero} não pode ser ocupado pois está {quarto.status.value}."):
        quarto.atualizarStatus(StatusQuarto.OCUPADO)