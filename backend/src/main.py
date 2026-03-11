from fastapi import FastAPI
from backend.src.api.routers import clientes_router
from backend.src.api.routers import quartos_router

app = FastAPI(title="SGH - Hotel API")

app.include_router(clientes_router.router)
app.include_router(quartos_router.router)