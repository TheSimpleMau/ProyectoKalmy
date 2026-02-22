import uuid
from sqlalchemy import Column, String, Float, Boolean, Integer
from .database import Base

class Item(Base):
    """
    Modelo de SQLAlchemy que representa la tabla 'item' en la base de datos.
    
    Almacena toda la información del inventario de libros.
    
    Atributos:
    - id: UUID generado automáticamente al crear el registro.
    - name, author: Tienen índices ('index=True') para optimizar las búsquedas en la base de datos.
    - available: Booleano que indica si el libro está a la venta.
    - stock: Cantidad de unidades físicas disponibles en el inventario.
    """

    __tablename__ = "item"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String, index=True)
    author = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    available = Column(Boolean, default=False)
    stock = Column(Integer, default=0)

class User(Base):
    """
    Modelo de SQLAlchemy que representa la tabla 'users' en la base de datos.
    
    Gestiona las credenciales y el nivel de acceso de las personas que utilizan el sistema.
    
    Atributos principales:
    - id: Clave primaria numérica autoincremental.
    - username: Nombre de usuario, el cual debe ser único ('unique=True') para evitar duplicados.
    - hashed_password: La contraseña encriptada.
    - role: Define los permisos del usuario (por defecto 'user').
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")

