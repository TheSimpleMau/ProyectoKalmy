# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import database, models, schemas, auth

router = APIRouter(tags=["auth"])

# Registro de usuario
@router.post("/register", 
            response_model=schemas.UserResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Registrar un nuevo usuario",
            response_description="El usuario recién creado (sin datos sensibles)",
            responses={
                400: {"description": "Imposible realizar acción."}
            })
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    Crea un nuevo usuario en la base de datos.
    Recibe las credenciales básicas y se encarga de aplicar un hash criptográfico a la contraseña antes de guardarla.
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Imposible realizar acción.")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Login
@router.post("/token", 
            response_model=schemas.Token,
            summary="Iniciar sesión y obtener token de acceso",
            response_description="Token JWT generado para la sesión",
            responses={
                401: {"description": "Usuario o contraseña incorrectos"}
            })
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    Autentica a un usuario y devuelve un token JWT válido para autorizar futuras peticiones a rutas protegidas.
    """
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}