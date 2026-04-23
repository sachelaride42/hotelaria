import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from backend.src.api.dependencies.seguranca import get_usuario_logado, exigir_gerente
from backend.src.domain.models.usuario import Gerente, Recepcionista

@pytest.mark.asyncio
@patch("backend.src.api.dependencies.seguranca.AuthService.verificar_token")
async def test_get_usuario_logado_sucesso(mock_verificar_token):
    """Retorna o usuário autenticado quando o token é válido e o e-mail existe no banco."""
    # Arrange
    mock_verificar_token.return_value = {"sub": "teste@hotel.com", "role": "GERENTE"}
    mock_repo = AsyncMock()
    usuario_falso = Gerente(nome="Teste", email="teste@hotel.com", senha_hash="123")
    mock_repo.buscar_por_email.return_value = usuario_falso

    # Act
    usuario_retornado = await get_usuario_logado(token="token_valido_qualquer", repo=mock_repo)

    # Assert
    assert usuario_retornado.email == "teste@hotel.com"
    mock_repo.buscar_por_email.assert_called_once_with("teste@hotel.com")

@pytest.mark.asyncio
@patch("backend.src.api.dependencies.seguranca.AuthService.verificar_token")
async def test_get_usuario_logado_token_invalido(mock_verificar_token):
    """Retorna 401 quando o token está corrompido ou expirado."""
    mock_verificar_token.return_value = None
    mock_repo = AsyncMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await get_usuario_logado(token="token_falso", repo=mock_repo)
        
    assert exc_info.value.status_code == 401
    assert "Credenciais inválidas" in exc_info.value.detail

@pytest.mark.asyncio
@patch("backend.src.api.dependencies.seguranca.AuthService.verificar_token")
async def test_get_usuario_logado_usuario_apagado(mock_verificar_token):
    """Retorna 401 quando o token é válido, mas o usuário não existe mais no banco."""
    mock_verificar_token.return_value = {"sub": "demitido@hotel.com"}

    mock_repo = AsyncMock()
    mock_repo.buscar_por_email.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_usuario_logado(token="token_valido", repo=mock_repo)
        
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_exigir_gerente_sucesso():
    """Permite o acesso quando o usuário autenticado possui o papel de Gerente."""
    usuario_gerente = Gerente(nome="Chefe", email="chefe@hotel.com", senha_hash="123")

    resultado = await exigir_gerente(usuario=usuario_gerente)
    assert resultado == usuario_gerente

@pytest.mark.asyncio
async def test_exigir_gerente_falha_para_recepcionista():
    """Retorna 403 quando o usuário autenticado possui o papel de Recepcionista."""
    usuario_rec = Recepcionista(nome="Atendente", email="atend@hotel.com", senha_hash="123")
    
    with pytest.raises(HTTPException) as exc_info:
        await exigir_gerente(usuario=usuario_rec)
        
    assert exc_info.value.status_code == 403
    assert "Acesso negado" in exc_info.value.detail