# app/auth.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import database, models, schemas

# --- Configuración ---
SECRET_KEY = "una_clave_muy_dificl_hecha_por_iop" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hashear contraseñas (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Habilita el botón de "Authorize" (el candado) en la documentación automática
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Verificar password (Login)
def verify_password(plain_password, hashed_password):
    """
    Compara una contraseña en texto plano con un hash encriptado (bcrypt).
    Retorna True si la contraseña coincide con el hash, de lo contrario False.
    """
    return pwd_context.verify(plain_password, hashed_password)

# Generar hash (Registro)
def get_password_hash(password):
    """
    Genera un hash seguro utilizando el algoritmo bcrypt a partir de una contraseña en texto plano.
    """
    return pwd_context.hash(password)

# Crear JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Crea y firma un JSON Web Token (JWT) para mantener la sesión del usuario.
    - **data**: Diccionario con la información a codificar (generalmente el 'sub' con el nombre de usuario).
    - **expires_delta**: Tiempo de validez del token. Si no se provee, expira en 15 minutos por defecto.
    Retorna el token codificado como un string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Validar JWT
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Dependencia de FastAPI para proteger rutas y obtener el usuario autenticado actualmente.
    1. Extrae el token JWT del encabezado 'Authorization: Bearer <token>'.
    2. Decodifica y valida la firma del token.
    3. Extrae el nombre de usuario y lo busca en la base de datos.
    
    Si el token es inválido, ha expirado, o el usuario ya no existe, lanza un error HTTP 401 Unauthorized.
    
    Retorna el objeto del usuario (models.User) si la validación es exitosa.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
        
    return user