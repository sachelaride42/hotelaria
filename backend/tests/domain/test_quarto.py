import pytest
from backend.src.domain.models.quarto import Quarto, StatusOcupacao, StatusLimpeza


def test_criar_quarto_com_valores_padrao():
    #Garante que um quarto novo nasce livre, limpo e na versão 1
    # Arrange & Act
    quarto = Quarto(numero="101", andar=1, tipo_quarto_id=1)

    # Assert
    assert quarto.numero == "101"
    assert quarto.andar == 1
    assert quarto.status_ocupacao == StatusOcupacao.LIVRE
    assert quarto.status_limpeza == StatusLimpeza.LIMPO
    assert quarto.tipo_quarto_id == 1
    assert quarto.versao == 1
    assert quarto.id is None


def test_atualizar_status_ocupacao_transicao_valida():
    """Testa a mudança normal de estado de ocupação do quarto"""
    # Arrange
    quarto = Quarto(numero="202", andar=2, tipo_quarto_id=2)
    assert quarto.status_ocupacao == StatusOcupacao.LIVRE

    # Act
    quarto.atualizarStatusOcupacao(StatusOcupacao.OCUPADO)

    # Assert
    assert quarto.status_ocupacao == StatusOcupacao.OCUPADO


def test_atualizar_status_ocupacao_impede_sujo_para_ocupado():
    #Testa a regra de negócio que impede alocar um hóspede em um quarto sujo.
    # Arrange
    quarto = Quarto(numero="303", andar=3, tipo_quarto_id=3, status_limpeza=StatusLimpeza.SUJO)

    # Act & Assert
    with pytest.raises(ValueError, match="Quarto precisa ser limpo antes de ser ocupado"):
        quarto.atualizarStatusOcupacao(StatusOcupacao.OCUPADO)


def test_atualizar_status_ocupacao_impede_manutencao_para_ocupado():
    # Garante que quartos em manutenção não sejam alocados no check-in
    # Arrange
    quarto = Quarto(numero="404", andar=4, tipo_quarto_id=1, status_ocupacao=StatusOcupacao.MANUTENCAO)

    # Act & Assert
    with pytest.raises(ValueError, match=f"O quarto {quarto.numero} não pode ser ocupado pois está {quarto.status_ocupacao.value}."):
        quarto.atualizarStatusOcupacao(StatusOcupacao.OCUPADO)


def test_checkout_auto_marca_quarto_sujo():
    """Ao liberar um quarto ocupado (checkout), o quarto deve ser marcado como sujo automaticamente."""
    # Arrange
    quarto = Quarto(numero="505", andar=5, tipo_quarto_id=1)
    quarto.atualizarStatusOcupacao(StatusOcupacao.OCUPADO)
    assert quarto.status_ocupacao == StatusOcupacao.OCUPADO
    assert quarto.status_limpeza == StatusLimpeza.LIMPO

    # Act
    quarto.atualizarStatusOcupacao(StatusOcupacao.LIVRE)

    # Assert
    assert quarto.status_ocupacao == StatusOcupacao.LIVRE
    assert quarto.status_limpeza == StatusLimpeza.SUJO


def test_atualizar_status_limpeza():
    """Governanta marca o quarto como limpo após a limpeza."""
    # Arrange
    quarto = Quarto(numero="606", andar=6, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)

    # Act
    quarto.atualizarStatusLimpeza(StatusLimpeza.LIMPO)

    # Assert
    assert quarto.status_limpeza == StatusLimpeza.LIMPO


def test_manutencao_nao_pode_ser_aplicada_a_quarto_ocupado():
    """Um quarto ocupado não pode entrar em manutenção."""
    # Arrange
    quarto = Quarto(numero="707", andar=7, tipo_quarto_id=1)
    quarto.atualizarStatusOcupacao(StatusOcupacao.OCUPADO)

    # Act & Assert
    with pytest.raises(ValueError, match=f"O quarto {quarto.numero} está ocupado e não pode entrar em manutenção."):
        quarto.atualizarStatusOcupacao(StatusOcupacao.MANUTENCAO)
