import pytest
from backend.src.domain.models.usuario import Gerente, Recepcionista, TipoUsuario
from backend.src.domain.services.auth_service import AuthService

def test_gerar_hash_e_verificar_senha():
    """Garante que o bcrypt gera um hash irreversível mas consegue validá-lo."""
    senha_plana = "minha_senha_super_secreta"
    
    # Act
    hash_gerado = Gerente.gerar_hash(senha_plana)
    gerente = Gerente(nome="João", email="joao@hotel.com", senha_hash=hash_gerado)
    
    # Assert
    assert hash_gerado != senha_plana
    assert gerente.verificar_senha(senha_plana) is True
    assert gerente.verificar_senha("senha_errada") is False

def test_instanciacao_polimorfica():
    """Garante que as classes filhas recebem o Enum correto automaticamente."""
    gerente = Gerente(nome="Admin", email="admin@hotel.com", senha_hash="123")
    recepcionista = Recepcionista(nome="Opera", email="opera@hotel.com", senha_hash="123")
    
    assert gerente.tipo == TipoUsuario.GERENTE
    assert recepcionista.tipo == TipoUsuario.RECEPCIONISTA

def test_criar_e_verificar_token_jwt():
    """Testa a engrenagem do python-jose para o JWT."""
    dados_payload = {"sub": "teste@hotel.com", "role": "GERENTE"}
    
    # Act
    token = AuthService.criar_token(dados_payload)
    payload_decodificado = AuthService.verificar_token(token)
    
    # Assert
    assert token is not None
    assert isinstance(token, str)
    assert payload_decodificado is not None
    assert payload_decodificado["sub"] == "teste@hotel.com"
    assert "exp" in payload_decodificado # Garante que a data de expiração foi injetada

def test_verificar_token_invalido():
    """Tokens adulterados ou lixo devem ser rejeitados imediatamente."""
    resultado = AuthService.verificar_token("token.totalmente.falso")
    assert resultado is None