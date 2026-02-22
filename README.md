# ProyectoKalmy - Librería Kalmy

> **Resumen:** Solución integral (API + Web) para la gestión de una librería desarrollada con **FastAPI**. El sistema implementa un CRUD completo, autenticación **JWT**, control de acceso por roles (**RBAC**), persistencia en **SQLite** y renderizado de vistas dinámicas con **Jinja2**.

![CI/CD Pipeline](https://github.com/thesimplemau/ProyectoKalmy/actions/workflows/ci.yml/badge.svg)

---

# Contenido

1. [Requerimientos Cumplidos](#requerimientos-cumplidos)
2. [Arquitectura y diseño](#arquitectura-y-diseño)
3. [Modelos y esquemas](#modelos-y-esquemas)
4. [Autenticación y autorización (RBAC)](#autenticación-y-autorización-rbac)
5. [Rutas / Endpoints importantes](#rutas--endpoints-importantes)
6. [Lógica de negocio destacada](#lógica-de-negocio-destacada)
7. [Inicialización y Seed de Datos](#inicialización-y-seed-de-datos)
8. [Batería de Tests](#tests)
9. [Instalación y ejecución](#instalación-y-ejecución)
10. [Mejoras y Consideraciones](#consideraciones-de-seguridad-y-mejoras-sugeridas)
11. [Estructura del proyecto](#estructura-del-proyecto-resumen-de-archivos)
12. [Licencia](#licencia)

---

## Requerimientos Cumplidos


* ✅ **Framework:** FastAPI (Python 3.10+).
* ✅ **Base de Datos:** SQLite con SQLAlchemy ORM.
* ✅ **CRUD Completo:** Endpoints para crear, leer (lista e individual), actualizar y eliminar.
* ✅ **Validaciones:** Uso exhaustivo de Pydantic para tipos de datos y restricciones (precios > 0, strings no vacíos).
* ✅ **Documentación:** OpenAPI (Swagger) totalmente configurado y enriquecido.
* ✅ **Tests Automatizados:** Pruebas unitarias y de integración con Pytest (cobertura de API, Web y Lógica).
* ⭐ **Bonus - Paginación:** Implementada en el catálogo (API y Web).
* ⭐ **Bonus - Autenticación:** Sistema JWT con roles diferenciados.
* ⭐ **Bonus - CI/CD:** Pipeline automatizado con GitHub Actions.

---

## Arquitectura y diseño

### Patrón de Diseño
Se utiliza una arquitectura modular inspirada en el patrón **MVC**:
* **Models (`app/models.py`)**: Definición de tablas y relaciones con SQLAlchemy.
* **Views (`app/templates/`)**: Plantillas HTML con Jinja2 para la experiencia de usuario web.
* **Controllers/Routers (`app/routers/`)**: Lógica de rutas separada por dominio (auth, items, web).

### Tecnologías Clave
* **FastAPI:** Alto rendimiento y validación automática.
* **Passlib (Bcrypt):** Hasheo seguro de contraseñas.
* **Python-Jose:** Generación y validación de tokens JWT.
* **Lifespan Events:** Gestión automática del ciclo de vida de la aplicación y la base de datos.

---

## Modelos y esquemas

### Modelos de Datos (SQLAlchemy)
* **Item:** Representa el libro. Utiliza **UUID** como identificador único para mayor seguridad y evitar la enumeración de recursos. Incluye campos de `stock` y `available`.
* **User:** Gestión de usuarios con campos para `username`, `hashed_password` y `role` (`admin`, `employee`, `user`).

### Validación (Pydantic)
Se definieron esquemas estrictos (`ItemCreate`, `ItemResponse`, etc.) utilizando `Field` para enriquecer la documentación de OpenAPI con ejemplos y restricciones de validación (como `gt=0` para precios y `ge=0` para stock).

---

## Autenticación y autorización (RBAC)

### Sistema de Doble Capa
1.  **JWT para API:** Los endpoints de la API REST se protegen mediante la dependencia `get_current_user` y el esquema OAuth2.
2.  **Cookies para Web:** Para la interfaz HTML, se utiliza una cookie `access_token` con la propiedad `httponly=True` para prevenir ataques XSS, permitiendo una experiencia de navegación fluida.

### Roles (RBAC)
* **Admin:** Acceso total (Lectura, Escritura, Edición, Eliminación).
* **Employee / User:** Acceso limitado a consulta y compra, con restricciones `403 Forbidden` en acciones administrativas.

---

## Lógica de negocio destacada

* **Gestión Automática de Disponibilidad:** Al realizar una compra o editar un libro, el sistema verifica el `stock`. Si este llega a 0, el campo `available` se marca automáticamente como `False`.
* **Paginación Inteligente:** Implementada con parámetros `skip` y `limit`. En la interfaz web, el cálculo de páginas se realiza dinámicamente (`math.ceil`) basándose en el total de registros.
* **Persistencia Segura:** Uso de sesiones de base de datos (`get_db`) gestionadas como dependencias para asegurar el cierre correcto de conexiones.

---

## Inicialización y Seed de Datos

El proyecto incluye un script de inicialización (`app/init_db.py`) que se ejecuta mediante el evento `lifespan` al arrancar la app.
* **Seed automático:** Si la base de datos está vacía, se insertan automáticamente ~60 libros y los 3 usuarios de prueba (`admin`, `empleado`, `test`).
* **Credenciales por defecto:**
    * Admin: `admin` / `admin123`
    * Employee: `empleado` / `empleado123`
    * User: `test` / `test123`

---

## Tests

La suite de pruebas en `test_main.py` utiliza una base de datos SQLite en memoria (`sqlite:///:memory:`) para garantizar un entorno limpio y rápido.
* **Tests de Integración:** Verifican el flujo completo de login -> obtención de token -> creación de item.
* **Tests de Seguridad:** Validan que los usuarios sin rol `admin` no puedan ejecutar DELETE o PUT.
* **Tests de UI:** Comprueban que Jinja2 renderice correctamente los datos de la base de datos en el HTML.
* **Lógica de Compra:** Test específico que simula compras sucesivas hasta agotar stock y verifica el cambio de estado del ítem.

---

## Instalación y ejecución

### Requisitos
* Python 3.10+
* Pip (gestor de paquetes)

### Instalación
1.  Clonar el repositorio.
    ```bash
    git clone https://github.com/TheSimpleMau/ProyectoKalmy.git
    ```
2.  Crear e instalar el entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    .\venv\Scripts\activate   # Windows
    pip install -r requirements.txt
    ```

### Ejecución
```bash
uvicorn app.main:app --reload
```

## Estructura del proyecto
```text
.
├── .github/workflows/ # Configuración de GitHub Actions
├── app/
│   ├── routers/
│   ├── templates/
│   ├── auth.py
│   ├── models.py
│   ├── database.py
│   ├── init_db.py
│   ├── main.py
│   ├── schemas.py
├── test_main.py
├── requirements.txt
└── database.db        # Generada automáticamente
```

# Licencia
---

## ⚖️ Licencia

Este proyecto está bajo la Licencia **MIT**. 
Consulta el archivo [LICENSE](LICENSE) para más detalles.

---
**Desarrollado por Mauricio Olguín Sánchez.**