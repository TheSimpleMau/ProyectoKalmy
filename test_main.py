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
    """
    Sobrescribe la dependencia de la base de datos de producción.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """
    Fixture de Pytest que prepara el entorno antes de cada prueba.
    """
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
    """
    Ayuda a iniciar sesión rápidamente en los tests
    """
    res = client.post("/token", data={"username": username, "password": password})
    return res.json()["access_token"]


# --- Sección de pruebas ---

# --- Pruebas de autenticación ---

def test_registro_usuario_exitoso():
    """Valida que un usuario nuevo pueda registrarse correctamente y devuelva código 201."""
    res = client.post("/register", json={"username": "nuevo", "password": "password123"})
    assert res.status_code == 201
    assert res.json()["username"] == "nuevo"

def test_registro_usuario_duplicado():
    """Valida que el sistema rechace el registro (código 400) si el nombre de usuario ya existe."""
    res = client.post("/register", json={"username": "user_test", "password": "password123"})
    assert res.status_code == 400

def test_login_credenciales_incorrectas():
    """Valida que se devuelva un error 401 Unauthorized al intentar iniciar sesión con una contraseña errónea."""
    res = client.post("/token", data={"username": "admin_test", "password": "mal"})
    assert res.status_code == 401


# --- Pruebas de la api (CRUD Y RBAC) ---

def test_obtener_lista_libros():
    """Verifica que el endpoint GET /items/ devuelva la lista de libros disponibles en la BD."""
    res = client.get("/items/")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["name"] == "Libro Base"

def test_obtener_libro_por_id_valido():
    """Verifica que se pueda recuperar la información detallada de un libro usando su ID (código 200)."""
    res = client.get("/items/libro-1")
    assert res.status_code == 200

def test_obtener_libro_inexistente():
    """Verifica que buscar un ID de libro que no existe devuelva un error 404."""
    res = client.get("/items/no-existe")
    assert res.status_code == 404

def test_admin_puede_crear_libro():
    """Valida el control de acceso (RBAC): Un usuario con rol 'admin' puede crear un libro nuevo (código 201)."""
    token = obtener_token("admin_test", "pass123")
    res = client.post(
        "/items/", 
        json={"name": "Nuevo", "author": "Bot", "description": "X", "price": 15.0, "stock": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Nuevo"

def test_usuario_normal_no_puede_borrar_libro():
    """Valida el control de acceso: Un usuario normal recibe un error 403 Forbidden al intentar borrar un libro."""
    token = obtener_token("user_test", "pass123")
    res = client.delete("/items/libro-1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


# --- Pruebas web (vistas y cookies) ---

def test_acceso_home_sin_login_redirige():
    """Comprueba que intentar acceder al catálogo web (/) sin sesión redirige al usuario a la página de login."""
    res = client.get("/", follow_redirects=False)
    assert res.status_code in [302, 303, 307]
    assert "/login" in res.headers["location"]

def test_login_web_crea_cookie():
    """Verifica que el inicio de sesión web exitoso inyecte correctamente la cookie 'access_token' y redirija al home."""
    res = client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    assert res.status_code in [302, 303]
    assert "/" in res.headers["location"]
    assert "access_token" in res.cookies

def test_borrar_libro_admin():
    """Verifica que un administrador autenticado vía web (cookies) pueda eliminar un libro y reciba un mensaje 200 JSON."""
    login_res = client.post("/login", data={"username": "admin_test", "password": "pass123"}, follow_redirects=False)
    cookie = login_res.cookies.get("access_token")
    client.cookies.set("access_token", cookie)
    
    res = client.delete("/delete/items/libro-1")
    client.cookies.clear()
    
    assert res.status_code == 200
    assert res.json() == {"message": "Libro eliminado"}

def test_borrar_libro_empleado_falla():
    """Verifica que un empleado autenticado vía web no tenga privilegios para borrar libros (error 403)."""
    login_res = client.post("/login", data={"username": "emp_test", "password": "pass123"}, follow_redirects=False)
    cookie = login_res.cookies.get("access_token")

    client.cookies.set("access_token", cookie)
    res = client.delete("/delete/items/libro-1")
    client.cookies.clear()
    
    assert res.status_code == 403


# --- Pruebas avanzadas y casos extremos ---

def test_logout_elimina_cookie_y_redirige():
    """Valida que al hacer logout se elimine la cookie de sesión y el usuario sea redirigido al login."""
    client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    res = client.get("/logout", follow_redirects=False)
    
    assert res.status_code in [302, 303, 307]
    assert "/login" in res.headers["location"]
    assert "access_token" not in client.cookies or not client.cookies.get("access_token")

def test_paginacion_web_funciona():
    """Comprueba que la página principal acepte el parámetro de paginación (?page=X) y lo procese sin lanzar errores."""
    login_res = client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))

    res = client.get("/?page=100")
    client.cookies.clear()
    
    assert res.status_code == 200
    assert "Página 100" in res.text

def test_crear_libro_mediante_formulario_web_admin():
    """Verifica el flujo completo de creación de un libro a través del formulario HTML (vía POST a /create)."""
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
    """Asegura que las protecciones RBAC de creación funcionen también desde peticiones JSON en la API para usuarios normales."""
    token = obtener_token("user_test", "pass123")
    res = client.post(
        "/items/", 
        json={"name": "Hacker", "author": "Hacker", "description": "Hacker", "price": 1, "stock": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403 

def test_usuario_normal_no_puede_editar_libro_api():
    """Asegura que un usuario normal reciba error 403 al intentar editar un libro vía API REST."""
    token = obtener_token("user_test", "pass123")
    res = client.put(
        "/items/libro-1", 
        json={"name": "Hacker Edit", "author": "Hacker", "description": "H", "price": 1, "stock": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


def test_comprar_libro_resta_stock_y_desactiva():
    """
    Simula la compra de las últimas 5 unidades de un libro.
    Valida que el stock llegue a 0 y que el sistema cambie automáticamente el estado 'available' a False.
    """
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
    """Verifica que el formulario de edición web actualice correctamente los datos del libro en la BD para un admin."""
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
    """Comprueba que un empleado no pueda mandar datos de edición a través de la ruta web protegida."""
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
    """Prueba de integridad: asegura que la base de datos de prueba efectivamente tiene registros cargados."""
    response = client.get("/items/")
    
    assert response.status_code == 200
    datos = response.json()
    
    assert len(datos) > 0, "¡La API no devuelve nada! La base de datos está vacía."

def test_verificar_renderizado_de_html():
    """
    Verifica la correcta integración entre Jinja2 y FastAPI.
    Asegura que el nombre del libro insertado en la BD realmente se esté imprimiendo en el código HTML de la respuesta.
    """
    login_res = client.post("/login", data={"username": "user_test", "password": "pass123"}, follow_redirects=False)
    client.cookies.set("access_token", login_res.cookies.get("access_token"))
    
    response = client.get("/") 
    assert response.status_code == 200
    
    html_content = response.text
    client.cookies.clear()
    
    assert "Libro Base" in html_content, "Los datos existen, pero no se renderizan en el HTML."