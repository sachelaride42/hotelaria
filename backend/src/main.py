from fastapi import FastAPI
from backend.src.api.routers import clientes_router, reservas_router, quartos_router, tipos_quarto_router

app = FastAPI(title="SGH - Hotel API")
app.include_router(clientes_router.router)
app.include_router(quartos_router.router)
app.include_router(reservas_router.router)
app.include_router(tipos_quarto_router.router)