import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Importar app y configuración
from app.main import app
from app.database import Base, get_db
from app.models import User, Item
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
    
    admin = User(username="admin_test", hashed_password=get_password_hash("pass123"), role="admin")
    empleado = User(username="emp_test", hashed_password=get_password_hash("pass123"), role="employee")
    usuario = User(username="user_test", hashed_password=get_password_hash("pass123"), role="user")
    
    libro = Item(
        id="libro-1", name="Libro Base", author="Autor", 
        description="Desc", price=10.0, available=True, stock=5
    )
    
    db.add_all([admin, empleado, usuario, libro])
    db.commit()
    db.close()
    
    yield # Se ejecutan las pruebas
    Base.metadata.drop_all(bind=engine)

# --- Función auxiliar ---
def obtener_token(username="admin_test", password="pass123"):
    """Ayuda a iniciar sesión rápidamente en los tests"""
    res = client.post("/token", data={"username": username, "password": password})
    return res.json()["access_token"]


# --- Sección de pruebas ---

# --- Pruebas de autenticación ---

def test_registro_usuario_exitoso():
    res = client.post("/register", json={"username": "nuevo", "password": "123"})
    assert res.status_code == 200
    assert res.json()["username"] == "nuevo"

def test_registro_usuario_duplicado():
    # El usuario "user_test" ya fue creado en el setup
    res = client.post("/register", json={"username": "user_test", "password": "123"})
    assert res.status_code == 400 # Bad Request

def test_login_credenciales_incorrectas():
    res = client.post("/token", data={"username": "admin_test", "password": "mal"})
    assert res.status_code == 401 # Unauthorized



# --- Pruebas de la api (CRUD Y RBAC) ---

def test_obtener_lista_libros():
    res = client.get("/items/")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["name"] == "Libro Base"

def test_obtener_libro_por_id_valido():
    res = client.get("/items/libro-1")
    assert res.status_code == 200

def test_obtener_libro_inexistente():
    res = client.get("/items/no-existe")
    assert res.status_code == 404

def test_admin_puede_crear_libro():
    token = obtener_token("admin_test", "pass123")
    res = client.post(
        "/items/", 
        json={"name": "Nuevo", "author": "Bot", "description": "X", "price": 15.0, "stock": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Nuevo"

def test_usuario_normal_no_puede_borrar_libro():
    token = obtener_token("user_test", "pass123")
    res = client.delete("/items/libro-1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


# --- Pruebas web (vistas y cookies) ---

def test_acceso_home_sin_login_redirige():
    res = client.get("/", follow_redirects=False)
    assert res.status_code in [302, 303, 307]
    assert "/login" in res.headers["location"]

def test_login_web_crea_cookie():
    res = client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    assert res.status_code in [302, 303]
    assert "/" in res.headers["location"]
    assert "access_token" in res.cookies

def test_borrar_libro_admin():
    login_res = client.post("/login", data={"username": "admin_test", "password": "pass123"}, follow_redirects=False)
    cookie = login_res.cookies.get("access_token")
    client.cookies.set("access_token", cookie)
    
    res = client.delete("/web/items/libro-1")
    client.cookies.clear()
    
    assert res.status_code == 200
    assert res.json() == {"message": "Libro eliminado"}

def test_borrar_libro_empleado_falla():
    login_res = client.post("/login", data={"username": "emp_test", "password": "pass123"}, follow_redirects=False)
    cookie = login_res.cookies.get("access_token")

    client.cookies.set("access_token", cookie)
    res = client.delete("/web/items/libro-1")
    client.cookies.clear()
    
    assert res.status_code == 403


# --- Pruebas avanzadas y casos extremos ---

def test_logout_elimina_cookie_y_redirige():
    client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    res = client.get("/logout", follow_redirects=False)
    
    assert res.status_code in [302, 303, 307]
    assert "/login" in res.headers["location"]
    assert "access_token" not in client.cookies or not client.cookies.get("access_token")

def test_paginacion_web_funciona():
    login_res = client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))

    res = client.get("/?page=100")
    client.cookies.clear()
    
    assert res.status_code == 200
    assert "Página 100" in res.text

def test_crear_libro_mediante_formulario_web_admin():
    login_res = client.post("/login", data={"username": "admin_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))
    
    form_data = {
        "name": "Libro desde HTML",
        "author": "Web",
        "price": "20.5",
        "description": "Prueba form",
        "stock": "10"
    }

    res = client.post("/create", data=form_data, follow_redirects=False)
    client.cookies.clear()
    
    assert res.status_code in [302, 303]
    assert "/" in res.headers["location"]

def test_usuario_normal_no_puede_crear_libro_api():
    token = obtener_token("user_test", "pass123")
    res = client.post(
        "/items/", 
        json={"name": "Hacker", "author": "Hacker", "description": "Hacker", "price": 0, "stock": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403 

def test_usuario_normal_no_puede_editar_libro_api():
    token = obtener_token("user_test", "pass123")
    res = client.put(
        "/items/libro-1", 
        json={"name": "Hacker Edit", "author": "Hacker", "description": "H", "price": 0, "stock": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


def test_comprar_libro_resta_stock_y_desactiva():
    login_res = client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))
    
    for _ in range(5):
        res = client.post("/buy/libro-1", follow_redirects=False)
        assert res.status_code in [302, 303]
        
    client.cookies.clear()
    res_api = client.get("/items/libro-1")
    libro_actualizado = res_api.json()
    
    assert libro_actualizado["stock"] == 0
    assert libro_actualizado["available"] == False


def test_admin_puede_editar_libro_web():
    login_res = client.post("/login", data={"username": "admin_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))
    
    form_data = {
        "name": "Libro Editado",
        "author": "Autor Editado",
        "price": "99.99",
        "description": "Nueva descripción",
        "stock": "50"
    }
    res = client.post("/edit/libro-1", data=form_data, follow_redirects=False)
    client.cookies.clear()
    
    assert res.status_code in [302, 303]
    res_api = client.get("/items/libro-1")
    assert res_api.json()["name"] == "Libro Editado"
    assert res_api.json()["price"] == 99.99

def test_empleado_no_puede_editar_libro_web():
    login_res = client.post("/login", data={"username": "emp_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))
    
    form_data = {"name": "Hacker", "author": "H", "price": "1", "description": "H", "stock": "1"}
    res = client.post("/edit/libro-1", data=form_data, follow_redirects=False)
    client.cookies.clear()
    
    assert res.status_code in [302, 303]
    
    res_api = client.get("/items/libro-1")
    assert res_api.json()["name"] != "Hacker"


# --- Visualización de los datos ---

def test_verificar_si_hay_datos_en_bd():
    response = client.get("/items/")
    
    assert response.status_code == 200
    datos = response.json()
    
    assert len(datos) > 0, "¡La API no devuelve nada! La base de datos está vacía."

def test_verificar_renderizado_de_html():
    login_res = client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))
    
    response = client.get("/") 
    assert response.status_code == 200
    
    html_content = response.text
    client.cookies.clear()
    
    assert "Libro Base" in html_content, "Los datos existen, pero no se renderizan en el HTML."