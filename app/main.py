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
app = FastAPI(
    title="Librería Kalmy",
    description="API para gestión de libros",
    version="1.0.0",
    lifespan=lifespan
)

# --- Template ---
templates = Jinja2Templates(directory="app/templates")

# --- Rutas ---
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(web.router)