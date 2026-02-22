# app/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

# --- Items ---

class ItemBase(BaseModel):
    name: str = Field(
        ..., 
        title="Nombre del libro", 
        min_length=1, 
        json_schema_extra={"example": "La sombra del viento"}
    )
    author: str = Field(
        ..., 
        title="Autor", 
        json_schema_extra={"example": "Carlos Ruiz Zafón"}
    )
    description: Optional[str] = Field(
        None, 
        title="Descripción", 
        json_schema_extra={"example": "Misterio literario en Barcelona"}
    )
    price: float = Field(
        ..., 
        title="Precio", 
        gt=0, 
        json_schema_extra={"example": 18.50}
    )
    available: bool = Field(
        False, 
        title="Disponibilidad", 
        description="Indica si el libro está a la venta"
    )
    stock: int = Field(
        0, 
        title="Stock disponible", 
        ge=0, 
        json_schema_extra={"example": 15}
    )

class ItemCreate(ItemBase):
    """
    Esquema para la creación de un nuevo libro.
    Hereda todos los atributos de validación de ItemBase.
    """
    pass

class ItemResponse(ItemBase):
    """
    Esquema de respuesta que representa un libro recuperado de la base de datos.
    """
    id: str = Field(
        ..., 
        title="ID del libro", 
        description="Identificador único (UUID) del libro", 
        json_schema_extra={"example": "123e4567-e89b-12d3-a456-426614174000"}
    )

    model_config = ConfigDict(from_attributes=True)

# --- USER ---
class UserBase(BaseModel):
    username: str = Field(
        ..., 
        title="Nombre de usuario", 
        description="El nombre de usuario único para el login", 
        min_length=3, 
        json_schema_extra={"example": "lector_curioso"}
    )

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        title="Contraseña", 
        description="La contraseña elegida por el usuario", 
        min_length=6, 
        json_schema_extra={"example": "MiSuperSecreto123"}
    )

class UserResponse(UserBase):
    id: int = Field(
        ..., 
        title="ID del usuario", 
        description="Identificador único numérico del usuario en la base de datos", 
        json_schema_extra={"example": 1}
    )

    model_config = ConfigDict(from_attributes=True)

# --- Token ---
class Token(BaseModel):
    access_token: str = Field(
        ..., 
        title="Token de acceso", 
        description="El JSON Web Token firmado para autenticar futuras peticiones.", 
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5c..."}
    )
    token_type: str = Field(
        ..., 
        title="Tipo de token", 
        description="El estándar del token de seguridad.", 
        json_schema_extra={"example": "bearer"}
    )

class TokenData(BaseModel):
    username: Optional[str] = Field(
        None, 
        title="Sujeto del token", 
        description="El nombre de usuario decodificado desde el token"
    )