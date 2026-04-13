import pytest
from backend.src.domain.models.usuario import Gerente, Recepcionista, TipoUsuario
from backend.src.infra.repositories.usuario_repository import UsuarioRepository, EmailDuplicadoError

@pytest.mark.asyncio
async def test_salvar_e_buscar_gerente(db_session):
    repo = UsuarioRepository(db_session)
    senha_segura = Gerente.gerar_hash("senha123")
    gerente = Gerente(nome="Alice", email="alice@hotel.com", senha_hash=senha_segura)
    
    # Act
    salvo = await repo.salvar(gerente)
    buscado = await repo.buscar_por_email("alice@hotel.com")
    
    # Assert: O repositório deve devolver exatamente uma instância de Gerente
    assert buscado is not None
    assert isinstance(buscado, Gerente) # Prova do Polymorphic Identity!
    assert buscado.tipo == TipoUsuario.GERENTE
    assert buscado.nome == "Alice"

@pytest.mark.asyncio
async def test_salvar_e_buscar_recepcionista(db_session):
    repo = UsuarioRepository(db_session)
    senha_segura = Recepcionista.gerar_hash("senha123")
    recepcionista = Recepcionista(nome="Bob", email="bob@hotel.com", senha_hash=senha_segura)
    
    # Act
    await repo.salvar(recepcionista)
    buscado = await repo.buscar_por_email("bob@hotel.com")
    
    # Assert: O repositório deve devolver exatamente uma instância de Recepcionista
    assert buscado is not None
    assert isinstance(buscado, Recepcionista) # Prova do Polymorphic Identity!
    assert buscado.tipo == TipoUsuario.RECEPCIONISTA

@pytest.mark.asyncio
async def test_impedir_email_duplicado(db_session):
    repo = UsuarioRepository(db_session)
    senha = Gerente.gerar_hash("123")
    
    await repo.salvar(Gerente(nome="Carlos", email="carlos@hotel.com", senha_hash=senha))
    
    # Tenta salvar outro usuário (mesmo que de cargo diferente) com o mesmo e-mail
    with pytest.raises(EmailDuplicadoError, match="Já existe um utilizador com este e-mail"):
        await repo.salvar(Recepcionista(nome="Carla", email="carlos@hotel.com", senha_hash=senha))