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


@pytest.mark.asyncio
async def test_buscar_usuario_por_id(db_session):
    """buscar_por_id deve retornar a entidade correta e None para IDs inexistentes."""
    repo = UsuarioRepository(db_session)
    salvo = await repo.salvar(Gerente(nome="Diana", email="diana@hotel.com", senha_hash=Gerente.gerar_hash("x")))

    encontrado = await repo.buscar_por_id(salvo.id)
    assert encontrado is not None
    assert isinstance(encontrado, Gerente)
    assert encontrado.email == "diana@hotel.com"

    nao_existe = await repo.buscar_por_id(9999)
    assert nao_existe is None


@pytest.mark.asyncio
async def test_atualizar_usuario(db_session):
    """salvar com id preenchido deve atualizar nome, email e hash."""
    repo = UsuarioRepository(db_session)
    original = await repo.salvar(Gerente(nome="Eduardo", email="edu@hotel.com", senha_hash=Gerente.gerar_hash("senha1")))

    # Simula a atualização: mesmo id, novos dados
    novo_hash = Gerente.gerar_hash("nova_senha")
    atualizado = Gerente(id=original.id, nome="Eduardo Silva", email="edusilva@hotel.com", senha_hash=novo_hash)
    salvo = await repo.salvar(atualizado)

    assert salvo.nome == "Eduardo Silva"
    assert salvo.email == "edusilva@hotel.com"

    # Confirma no banco
    buscado = await repo.buscar_por_id(original.id)
    assert buscado.nome == "Eduardo Silva"


@pytest.mark.asyncio
async def test_deletar_usuario(db_session):
    """deletar deve remover o registro; buscar_por_id retorna None depois."""
    repo = UsuarioRepository(db_session)
    usuario = await repo.salvar(Recepcionista(nome="Fábio", email="fabio@hotel.com", senha_hash=Recepcionista.gerar_hash("x")))

    await repo.deletar(usuario.id)

    assert await repo.buscar_por_id(usuario.id) is None


@pytest.mark.asyncio
async def test_deletar_usuario_inexistente_nao_lanca_erro(db_session):
    """deletar um id inexistente não deve lançar exceção."""
    repo = UsuarioRepository(db_session)
    await repo.deletar(9999)  # Não deve levantar nada