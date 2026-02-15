from fastapi import APIRouter, Request, Depends, Cookie, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from .. import database, models, auth

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(include_in_schema=False)

# --- Login ---
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_logic(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user or not auth.verify_password(password, user.hashed_password):
        # Si falla, volvemos a mostrar el HTML pero con un mensaje de error
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuario o contraseña incorrectos" # Esto se verá en el HTML
        })
    
    access_token = auth.create_access_token(data={"sub": user.username})
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True
    )
    
    return response

# --- Logout ---
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# --- Home ---
@router.get("/")
def home(
    request: Request, 
    db: Session = Depends(database.get_db),
    access_token: str | None = Cookie(default=None)
):
    if not access_token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    try:
        token_limpio = access_token.replace("Bearer ", "")
        
        payload = jwt.decode(token_limpio, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise JWTError()
            
    except JWTError:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    books = db.query(models.Book).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "books": books,
        "title": "Librería FastAPI + Pico.css",
        "user": username
    })