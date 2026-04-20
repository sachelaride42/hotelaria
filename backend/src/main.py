from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importação de todos os routers que construímos
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
    governanca_router
)

# Inicializa a aplicação FastAPI com os metadados do TCC
app = FastAPI(
    title="API do Sistema de Gestão Hoteleira",
    description="Backend construído para o Trabalho de Conclusão de Curso (TCC).",
    version="1.0.0"
)

# Configuração do CORS (Cross-Origin Resource Sharing)
# Permite que o frontend (mesmo rodando noutra porta, ex: localhost:3000) faça requisições à API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitui "*" pelos domínios reais do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Registo dos Routers (Os Módulos do Sistema)
# ==========================================

# 1. Autenticação e Utilizadores
app.include_router(auth_router.router, prefix="/auth")
app.include_router(usuarios_router.router)

# 2. Cadastros Base
app.include_router(clientes_router.router)
app.include_router(tipos_quarto_router.router)
app.include_router(quartos_router.router)
app.include_router(produtos_servicos_router.router)

# 3. Operação Hoteleira
app.include_router(reservas_router.router)
app.include_router(hospedagens_router.router)
app.include_router(itens_consumo_router.router)

# 4. Governança
app.include_router(governanca_router.router)

@app.get("/", tags=["Health Check"])
async def root():
    """Rota raiz para verificar se o servidor está online."""
    return {"status": "online", "mensagem": "API do Hotel a funcionar perfeitamente!"}