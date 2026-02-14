# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routers import books
from .init_db import create_tables

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield
    print("Hasta la próxima!")

# --- Inicialización de la app ---
app = FastAPI(
    title="Librería API",
    description="API profesional para gestión de libros",
    version="1.0.0",
    lifespan=lifespan
)

# --- RUTAS ---
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Librería API. Ve a /docs para comenzar."}

# Incluimos los routers (Controladores)
app.include_router(books.router)