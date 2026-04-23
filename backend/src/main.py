from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.src.api.routers import (
    auth_router,
    usuarios_router,
    tipos_quarto_router,
    quartos_router,
    clientes_router,
    reservas_router,
    hospedagens_router,
    produtos_servicos_router,
    itens_consumo_router,
    governanca_router,
    pagamentos_router
)
from backend.src.infra.database import AsyncSessionLocal
from backend.src.infra.orm_models.usuario_orm import GerenteORM
from backend.src.domain.models.usuario import TipoUsuario, Usuario


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executado na inicialização e no encerramento da API."""
    # --- STARTUP ---
    async with AsyncSessionLocal() as session:
        resultado = await session.execute(
            select(GerenteORM).where(GerenteORM.tipo == TipoUsuario.GERENTE)
        )
        gerente_existente = resultado.scalars().first()

        if not gerente_existente:
            senha_hash = Usuario.gerar_hash("admin123")
            gerente_padrao = GerenteORM(
                nome="Administrador",
                email="admin@hotel.com",
                senha_hash=senha_hash,
                tipo=TipoUsuario.GERENTE,
            )
            session.add(gerente_padrao)
            await session.commit()
            print("✅ Gerente padrão criado  →  email: admin@hotel.com  |  senha: admin123")
        else:
            print(f"✅ Gerente já existe: {gerente_existente.email}")

    yield


app = FastAPI(
    title="API do Sistema de Gestão Hoteleira",
    description="Backend construído para o Trabalho de Conclusão de Curso (TCC).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substituir por domínios específicos do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/auth")
app.include_router(usuarios_router.router)
app.include_router(clientes_router.router)
app.include_router(tipos_quarto_router.router)
app.include_router(quartos_router.router)
app.include_router(produtos_servicos_router.router)
app.include_router(reservas_router.router)
app.include_router(hospedagens_router.router)
app.include_router(itens_consumo_router.router)
app.include_router(pagamentos_router.router)
app.include_router(governanca_router.router)

@app.get("/", tags=["Health Check"])
async def root():
    """Rota raiz para verificar se o servidor está online."""
    return {"status": "online", "mensagem": "API do Hotel a funcionar perfeitamente!"}