# ProyectoKalmy
# README.md — Librería Kalmy

> **Resumen rápido:** Proyecto web/API para gestionar una librería (catálogo de libros) con **FastAPI**, vistas HTML con **Jinja2**, autenticación por **JWT**, control de roles (RBAC) y persistencia en **SQLite**. Incluye rutas públicas y protegidas (API y web), inicialización automática de la BD con datos de ejemplo y una batería de tests automatizados con `pytest`.
> Código completo y todos los archivos están en el archivo que me compartiste. 

---

# Contenido

1. [Qué hace el sistema](#qué-hace-el-sistema)
2. [Arquitectura y diseño](#arquitectura-y-diseño)
3. [Modelos y esquemas](#modelos-y-esquemas)
4. [Autenticación y autorización (RBAC)](#autenticación-y-autorización-rbac)
5. [Rutas / Endpoints importantes](#rutas--endpoints-importantes)
6. [Lógica de negocio importante](#lógica-de-negocio-importante)
7. [Inicialización y datos dummy](#inicialización-y-datos-dummy)
8. [Tests](#tests)
9. [Instalación y ejecución](#instalación-y-ejecución)
10. [Consideraciones de seguridad y mejoras sugeridas](#consideraciones-de-seguridad-y-mejoras-sugeridas)
11. [Estructura del proyecto (resumen de archivos)](#estructura-del-proyecto-resumen-de-archivos)

---

## Qué hace el sistema

* Exponer una **API REST** para gestionar libros (`/items`) con operaciones CRUD.
* Proveer una **interfaz web** (páginas HTML) para ver el catálogo, comprar libros y realizar acciones administrativas (crear/editar/borrar) a través de formularios.
* Manejar **autenticación** con JWT (endpoint `/token`) y sesiones web mediante cookie `access_token` (httponly).
* Implementar **Control de Acceso por Roles (RBAC)** con roles `admin`, `employee`, `user`.
* Mantener persistencia en **SQLite** y crear/sembrar la BD al iniciar la app.
* Contar con pruebas automáticas que cubren autenticación, RBAC, vistas web y lógica de negocio.

---

## Arquitectura y diseño

### Patrón MVC (adaptado)

* **Models**: `app/models.py` — definición de entidades `Item` y `User` (SQLAlchemy).
* **Views**: `app/templates/*` — páginas HTML renderizadas por Jinja2 (index, login, edit, etc.).
* **Controllers**: Routers en `app/routers/*` y `app/web.py` — controlan la lógica de las rutas API y web.

  * `app/routers/items.py` → API REST para `items`.
  * `app/routers/auth.py` → endpoints de registro y token (API).
  * `app/web.py` → páginas web (login, home, create/edit/delete vía web, compra).

### Dependencias clave

* FastAPI (web + API), Uvicorn (servidor), SQLAlchemy (ORM), Jinja2 (templates), `python-jose` (JWT), `passlib[bcrypt]` (hash de contraseñas), `python-multipart` (formularios), pytest (tests).

### Ciclo de vida

* `app/main.py` registra los routers y define un `lifespan` que llama `create_tables()` en `app/init_db.py` para crear y sembrar la BD al inicio.

---

## Modelos y esquemas

### Modelos (SQLAlchemy)

* **Item**

  * `id: str` (UUID string)
  * `name`, `author`, `description`, `price`
  * `stock: int`, `available: bool`
* **User**

  * `id: int` (auto incremental)
  * `username: str`, `hashed_password: str`
  * `role: str` (default `"user"`)

### Schemas (Pydantic)

* `ItemCreate`, `ItemResponse` — validación/serialización para API.
* `UserCreate`, `UserResponse` — creación y respuesta de usuario.
* `Token`, `TokenData` — esquema para JWT.

Los `response_model` en los endpoints usan esas clases para asegurar contratos API.

---

## Autenticación y autorización (RBAC)

### JWT para API

* `app/auth.py` define:

  * `SECRET_KEY`, `ALGORITHM`, expiración de token (configurable por `ACCESS_TOKEN_EXPIRE_MINUTES`).
  * `create_access_token()` para firmar JWT.
  * `get_current_user()` dependency que valida token OAuth2 (`OAuth2PasswordBearer`) y obtiene el usuario de la BD.

### Login para web

* `app/web.py` maneja formularios de login. Si el login tiene éxito:

  * crea JWT con `auth.create_access_token(...)`
  * setea cookie `access_token` con `httponly=True` (no accesible desde JS).
* `get_user_from_cookie()` decodifica el JWT de la cookie para identificar al usuario en las vistas.

### RBAC (roles)

* `User.role` almacena el rol (`admin`, `employee`, `user`).
* En endpoints críticos (crear/editar/eliminar libros vía API o web) se comprueba `current_user.role != "admin"` y se lanza `HTTPException(status_code=403)` para evitar acciones no autorizadas.
* En `web.py` se protege páginas y acciones web revisando `current_user` y `user.role`.

---

## Rutas / Endpoints importantes

### API (`/items`)

* `GET /items/` — lista pública (con `skip` y `limit`).
* `GET /items/{item_id}` — obtener detalle libro.
* `POST /items/` — crear (admin).
* `PUT /items/{item_id}` — actualizar (admin).
* `DELETE /items/{item_id}` — borrar (admin).

### Autenticación (API)

* `POST /register` — crear usuario (router `auth`).
* `POST /token` — login (OAuth2PasswordRequestForm), devuelve `access_token` y `token_type`.

### Web (vistas, rutas no documentadas en docs)

* `GET /login` — formulario de login.
* `POST /login` — procesa login y setea cookie.
* `GET /logout` — borra cookie y redirige.
* `GET /` — home (HTML), paginación (`page`), requiere cookie válida.
* `POST /buy/{item_id}` — compra (reduce `stock`, marca `available=False` si stock=0).
* `POST /create` — crear libro vía HTML (admin).
* `GET/POST /edit/{item_id}` — editar libro (admin).
* `DELETE /web/items/{item_id}` — eliminar libro (admin), devuelve JSON.

---

## Lógica de negocio importante

* **Compra (`/buy/{item_id}`)**: si hay stock y `available` true, se decrementa `stock`. Si `stock` llega a 0, `available` se pone en `False`. Operación segura para evitar ventas cuando no hay stock.
* **Paginación en home**: límite fijo `LIMIT = 6`, cálculo de `offset` y `total_pages` (usa `math.ceil`).
* **Disponibilidad vs stock**: `available` se deriva de `stock > 0` al crear/editar y al sembrar datos iniciales.
* **Semilla de datos**: `init_db.create_tables()` si la tabla `Item` está vacía, inserta un conjunto amplio de libros y asigna stock aleatorio a los disponibles.

---

## Inicialización y datos dummy

* `app/init_db.py` crea las tablas (metadata.create_all) y:

  * Si no hay `Item`, inserta ~60 libros de muestra (lista en el archivo).
  * Si no hay `User`, crea tres usuarios por defecto:

    * `admin` / `admin123` (rol `admin`)
    * `empleado` / `empleado123` (rol `employee`)
    * `test` / `test123` (rol `user`)
* `create_tables()` se invoca en el `lifespan` de la app en `main.py`, por lo que ocurre al arrancar la aplicación.

---

## Tests

* `test_main.py` usa `TestClient` y una base de datos en memoria (`sqlite:///:memory:` y `StaticPool`) para pruebas aisladas.
* Hace override de la dependencia `get_db` para usar `TestingSessionLocal`.
* Cubre:

  * Registro y login (API).
  * RBAC: admin puede crear/editar/borrar; usuarios normales no.
  * Endpoints públicos y privados.
  * Flujo web: login via form, cookie `access_token`, redirecciones, compra de libro (stock decrementa hasta desactivar), paginación, creación/edición via formulario.
* Buen ejemplo de cómo testear tanto API (Bearer token) como vistas (cookies).

---

## Instalación y ejecución

### Requisitos (ejemplos)

* Python 3.10+
* Recomendado usar virtualenv / venv.

### Dependencias (ejemplo `requirements.txt`)

```
fastapi
uvicorn[standard]
SQLAlchemy
jinja2
python-jose[cryptography]
passlib[bcrypt]
python-multipart
pytest
requests
```

### Ejecutar localmente

1. Crear entorno:

```bash
python -m venv .venv
source .venv/bin/activate    # mac/linux
.\.venv\Scripts\activate     # windows
pip install -r requirements.txt
```

2. Iniciar la app:

```bash
uvicorn app.main:app --reload
```

* Al arrancar, `init_db.create_tables()` sembrará la BD `./database.db` si está vacía.

3. Documentación automática:

* OpenAPI: `http://127.0.0.1:8000/docs` (puedes usar el botón *Authorize* gracias a `oauth2_scheme`).

4. Ejecutar tests:

```bash
pytest -q
```

---

## Consideraciones de seguridad y mejoras sugeridas

### Observaciones de seguridad detectadas en el código actual

* `SECRET_KEY` está **hardcodeada** en `app/auth.py`. Recomendación: usar variables de entorno (p. ej. `os.environ["SECRET_KEY"]`) y no almacenar claves en el repo.
* Cookie `access_token` tiene `httponly=True` (bueno) pero no se marca `secure=True` (necesario en producción HTTPS).
* No hay protección explícita CSRF para formularios (aunque cookie es httponly y las acciones mutantes usan POST/DELETE, considerar CSRF token si se expone a navegadores inseguros).
* Expiración de token por defecto relativamente corta (30 minutos en la configuración actual) — ajustar según necesidades y refresh tokens si se desea experiencia de usuario más fluida.
* Revisar manejo de excepciones en decodificado de JWT: `except:` genérico en `get_user_from_cookie` — al loggear errores puede ayudar al diagnóstico.

### Mejoras funcionales y tecnológicas

* Mover la configuración sensible (SECRET_KEY, DB URL, token expiry) a un `config` central o usar `pydantic.BaseSettings`.
* Añadir endpoints para gestión de usuarios (crear/editar roles) protegidos para administradores.
* Implementar **refresh tokens** y revocación de tokens (lista negra).
* Migración a una BD más robusta (Postgres) si se necesita concurrencia real y despliegue en producción.
* Tests de integración / CI (GitHub Actions) que ejecuten `pytest` en cada PR.
* Añadir logging estructurado y métricas.

---

## Estructura del proyecto (resumen)

```
app/
  main.py
  auth.py
  database.py
  init_db.py
  models.py
  schemas.py
  templates/
  routers/
    auth.py
    items.py
  web.py
tests/
  test_main.py
database.db (sqlite)        # creado al ejecutar
requirements.txt
README.md
```

---

## Contacto y licencia

* Autor: Mauricio Olguín Sánchez.
* Licencia: MIT.