import pytest
from backend.src.domain.models.cliente import Cliente


def test_criar_cliente_com_dados_minimos_obrigatorios():
    """Testa a regra de negócio do cadastro rápido (apenas nome e telefone)"""
    # Arrange & Act
    cliente = Cliente(nome="Mateus Roberto", telefone="67999999999")

    # Assert
    assert cliente.nome == "Mateus Roberto"
    assert cliente.telefone == "67999999999"
    assert cliente.cpf is None
    assert cliente.email is None


def test_criar_cliente_com_todos_os_dados_validos():
    """Testa a criação de um cliente completo, incluindo a formatação do CPF"""
    # Arrange & Act
    cliente = Cliente(
        nome="Lucas da Silva",
        telefone="67988888888",
        cpf="111.222.333-44",
        email="lucas@email.com"
    )

    # Assert
    assert cliente.nome == "Lucas da Silva"
    assert cliente.cpf == "111.222.333-44"  # O CPF original deve ser mantido na propriedade
    assert cliente.email == "lucas@email.com"


def test_cliente_sem_nome_lanca_excecao():
    """Garante a Exceção: O campo Nome é obrigatório"""
    with pytest.raises(ValueError, match="O campo 'Nome' é obrigatório"):
        Cliente(nome="", telefone="67999999999")

    with pytest.raises(ValueError, match="O campo 'Nome' é obrigatório"):
        Cliente(nome="   ", telefone="67999999999")  # Testa strings com apenas espaços


def test_cliente_sem_telefone_lanca_excecao():
    """Garante que não exista cliente incontactável no sistema"""
    with pytest.raises(ValueError, match="O campo 'Telefone' é obrigatório"):
        Cliente(nome="João", telefone="")


def test_cliente_com_cpf_tamanho_invalido_lanca_excecao():
    """O CPF precisa ter exatamente 11 dígitos após a limpeza"""
    with pytest.raises(ValueError, match="CPF inválido"):
        Cliente(nome="Maria", telefone="11999999999", cpf="123456789")  # Faltam dígitos

    with pytest.raises(ValueError, match="CPF inválido"):
        Cliente(nome="Maria", telefone="11999999999", cpf="123.456.789-000")  # Sobram dígitos


def test_cliente_com_cpf_letras_lanca_excecao():
    """O CPF não pode conter letras"""
    with pytest.raises(ValueError, match="CPF inválido"):
        Cliente(nome="Pedro", telefone="11999999999", cpf="111.AAA.333-44")