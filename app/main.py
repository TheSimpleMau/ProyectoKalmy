from fastapi import FastAPI

app = FastAPI(
    title="API de Items",
    description="API para gestión de items con FastAPI",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"mensaje": "Hola mundo!."}

@app.get("/saludo/{nombre}")
def read_item(nombre: str):
    return {"saludo": f"Hola, {nombre}!"}   