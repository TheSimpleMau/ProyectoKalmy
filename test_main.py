import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Importar app y configuración
from app.main import app
from app.database import Base, get_db
from app.models import User
from app.auth import get_password_hash

# Crear base de datos
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    admin_user = User(
        username="admin_test", 
        hashed_password=get_password_hash("secreta123"), 
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    db.close()
    
    yield 

    Base.metadata.drop_all(bind=engine)


# --- Pruebas --- 

# --- Rutas Públicas ---
def test_leer_libros_api_vacia():
    response = client.get("/books/")
    
    assert response.status_code == 200
    assert response.json() == []

# --- Registro de Usuario ---
def test_registro_usuario_nuevo():
    response = client.post(
        "/register",
        json={"username": "usuario_nuevo", "password": "mipassword"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "usuario_nuevo"
    assert "id" in data

# --- Login y Control de Acceso ---
def test_login_y_crear_libro_como_admin():
    login_response = client.post(
        "/token",
        data={"username": "admin_test", "password": "secreta123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    libro_nuevo = {
        "name": "Libro de Prueba",
        "author": "Bot",
        "price": 10.5,
        "description": "Un libro automático",
        "stock": 5
    }
    
    create_response = client.post("/books/", json=libro_nuevo, headers=headers)
    
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Libro de Prueba"