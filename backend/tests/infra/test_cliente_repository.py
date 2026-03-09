import pytest
from backend.src.domain.models.cliente import Cliente
from backend.src.infra.repositories.cliente_repository import ClienteRepository, CPFDuplicadoError


@pytest.mark.asyncio
async def test_salvar_e_buscar_cliente_por_id(db_session):
    """Testa se o ORM persiste os dados corretamente."""
    repo = ClienteRepository(db_session)
    cliente = Cliente(nome="Mateus Roberto", telefone="67999999999", email="mateus@teste.com")

    # Act
    cliente_salvo = await repo.salvar(cliente)
    cliente_buscado = await repo.buscar_por_id(cliente_salvo.id)

    # Assert
    assert cliente_buscado is not None
    assert cliente_buscado.nome == "Mateus Roberto"
    assert cliente_buscado.id == cliente_salvo.id


@pytest.mark.asyncio
async def test_buscar_cliente_por_nome_parcial(db_session):
    """Testa a busca ILIKE (ignorando maiúsculas e buscando trechos)."""
    repo = ClienteRepository(db_session)
    await repo.salvar(Cliente(nome="Lucas Silva", telefone="111"))
    await repo.salvar(Cliente(nome="Ana Silveira", telefone="222"))
    await repo.salvar(Cliente(nome="Marcos Paulo", telefone="333"))

    # Act: Buscando por "silv" (deve achar Lucas e Ana)
    resultados = await repo.buscar_por_nome("silv")

    assert len(resultados) == 2


@pytest.mark.asyncio
async def test_impedir_cadastro_de_cpf_duplicado(db_session):
    """Testa a Exceção (Unicidade de CPF no banco de dados)."""
    repo = ClienteRepository(db_session)
    cliente1 = Cliente(nome="João", telefone="111", cpf="12345678901")
    cliente2 = Cliente(nome="Maria", telefone="222", cpf="12345678901")  # Mesmo CPF

    await repo.salvar(cliente1)

    # Deve estourar o erro customizado quando tentar salvar a Maria
    with pytest.raises(CPFDuplicadoError, match="CPF já cadastrado"):
        await repo.salvar(cliente2)