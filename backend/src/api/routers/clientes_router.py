from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from backend.src.infra.database import get_db_session
from backend.src.infra.repositories.cliente_repository import ClienteRepository, CPFDuplicadoError
from backend.src.domain.models.cliente import Cliente
from backend.src.api.schemas.cliente_schema import ClienteCriarInput, ClienteAtualizarInput, ClienteOutput
from backend.src.api.dependencies.seguranca import get_usuario_logado, exigir_gerente

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(get_usuario_logado)]
)


def get_cliente_repo(session: AsyncSession = Depends(get_db_session)) -> ClienteRepository:
    return ClienteRepository(session)


@router.post("/", response_model=ClienteOutput, status_code=status.HTTP_201_CREATED)
async def criar_cliente(
        payload: ClienteCriarInput,
        repo: ClienteRepository = Depends(get_cliente_repo)
):
    """Cadastrando um Novo Cliente"""
    try:
        # Ao instanciar o Cliente, o __post_init__ é disparado
        novo_cliente = Cliente(
            nome=payload.nome,
            telefone=payload.telefone,
            cpf=payload.cpf,
            email=payload.email
        )
        cliente_salvo = await repo.salvar(novo_cliente)
        return cliente_salvo

    except ValueError as erro_dominio:
        # Exceção: Falta de dados ou CPF inválido
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro_dominio))
    except CPFDuplicadoError as erro_banco:
        # Exceção: CPF já existe no banco
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro_banco))


@router.get("/", response_model=List[ClienteOutput])
async def buscar_clientes(
        nome: Optional[str] = Query(None, description="Busca parcial pelo nome"),
        cpf: Optional[str] = Query(None, description="Busca exata pelo CPF"),
        repo: ClienteRepository = Depends(get_cliente_repo)
):
    """Selecionando Cliente Existente"""
    if cpf:
        cliente = await repo.buscar_por_cpf(cpf)
        return [cliente] if cliente else []

    if nome:
        return await repo.buscar_por_nome(nome)

    return []


@router.put("/{cliente_id}", response_model=ClienteOutput)
async def atualizar_cliente(
        cliente_id: int,
        payload: ClienteAtualizarInput,
        repo: ClienteRepository = Depends(get_cliente_repo)
):
    """Editando Dados de um Cliente Existente"""
    cliente_existente = await repo.buscar_por_id(cliente_id)
    if not cliente_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

    try:
        # Instanciando um novo objeto Cliente força-se a validação do __post_init__ novamente
        cliente_atualizado = Cliente(
            id=cliente_existente.id,
            nome=payload.nome,
            telefone=payload.telefone,
            cpf=payload.cpf,
            email=payload.email
        )
        cliente_salvo = await repo.salvar(cliente_atualizado)
        return cliente_salvo

    except ValueError as erro_dominio:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro_dominio))
    except CPFDuplicadoError as erro_banco:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro_banco))


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(exigir_gerente)])
async def deletar_cliente(
        cliente_id: int,
        repo: ClienteRepository = Depends(get_cliente_repo)
):
    """Remove um cliente do sistema. Exige permissão de Gerente."""
    cliente = await repo.buscar_por_id(cliente_id)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    try:
        await repo.deletar(cliente_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível remover o cliente pois ele possui reservas ou hospedagens vinculadas."
        )