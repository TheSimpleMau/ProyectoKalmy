# app/main.py
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from .routers import auth, items, web
from .init_db import create_tables

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield
    print("Hasta la próxima!")

# --- Inicialización de la app ---

tags_metadata = [
    {
        "name": "auth",
        "description": "Operaciones con usuarios. Incluye el registro y el inicio de sesión.",
    },
    {
        "name": "items",
        "description": "Gestión del inventario de libros. Permite crear, leer, actualizar y borrar (CRUD).",
    }
]

app = FastAPI(
    title="Librería Kalmy",
    description="API para gestión de libros",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# --- Template ---
templates = Jinja2Templates(directory="app/templates")

# --- Rutas ---
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(web.router)