import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_criar_usuario_sucesso(client: AsyncClient):
    payload = {
        "nome": "Carlos Gerente",
        "email": "carlos@hotel.com",
        "senha": "senha_forte_123",
        "tipo": "GERENTE"
    }
    
    response = await client.post("/usuarios/", json=payload)
    
    assert response.status_code == 201
    dados = response.json()
    assert dados["nome"] == "Carlos Gerente"
    assert dados["email"] == "carlos@hotel.com"
    assert "senha" not in dados # REGRA DE OURO: A senha nunca deve voltar na resposta!

@pytest.mark.asyncio
async def test_api_impedir_email_duplicado(client: AsyncClient):
    payload = {
        "nome": "Ana Recepcão",
        "email": "ana@hotel.com",
        "senha": "123456",
        "tipo": "RECEPCIONISTA"
    }
    
    # 1. Cria a primeira vez (Sucesso)
    primeiro = await client.post("/usuarios/", json=payload)
    print(primeiro.json())
    assert primeiro.status_code == 201

    # 2. Tenta criar de novo (Falha)
    response = await client.post("/usuarios/", json=payload)
    assert response.status_code == 409
    assert "Já existe um utilizador" in response.json()["detail"]