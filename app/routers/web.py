from fastapi import APIRouter, Request, Depends, Cookie, status, Form, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import jwt
from .. import database, models, auth
import math

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(include_in_schema=False)

# --- Funciones auxiliares ---
def get_user_from_cookie(access_token: str | None = Cookie(default=None), db: Session = Depends(database.get_db)):
    if not access_token: return None
    try:
        token_limpio = access_token.replace("Bearer ", "")
        payload = jwt.decode(token_limpio, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username = payload.get("sub")
        return db.query(models.User).filter(models.User.username == username).first()
    except:
        return None

# --- Login ---
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

@router.post("/login")
def login_logic(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "login.html", {
                "request": request,
                "error": "Usuario o contraseña incorrectos"
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
    user = Depends(get_user_from_cookie),
    page: int = Query(1, ge=1)
):
    if not user: return RedirectResponse("/login")
    LIMIT = 6
    offset = (page - 1) * LIMIT
    
    total_books = db.query(models.Book).count()
    total_pages = math.ceil(total_books / LIMIT)
    
    books = db.query(models.Book).offset(offset).limit(LIMIT).all()
    
    return templates.TemplateResponse(request, "index.html", {
        "request": request, 
        "books": books,
        "title": "Librería Chida",
        "user": user,
        "page": page,
        "total_pages": total_pages
    })

@router.post("/buy/{book_id}")
def buy_book(
    book_id: str, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_user_from_cookie)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    
    if db_book and db_book.stock > 0 and db_book.available:
        db_book.stock -= 1
        
        if db_book.stock == 0:
            db_book.available = False
            
        db.commit()
        db.refresh(db_book)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# --- Aciones de Admin --- 

# --- Borrar libro ---
@router.delete("/web/books/{book_id}")
def delete_book(book_id: str, db: Session = Depends(database.get_db), user = Depends(get_user_from_cookie)):
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book:
        db.delete(book)
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Libro eliminado"})
    return JSONResponse(status_code=404, content={"message": "Libro no encontrado"})

# --- Crear libro ---
@router.post("/create")
def create_book_web(
    name: str = Form(...),
    author: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    stock: int = Form(...),
    db: Session = Depends(database.get_db), 
    user = Depends(get_user_from_cookie)
):
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")

    is_available = stock > 0

    new_book = models.Book(
        name=name, author=author, price=price, 
        description=description, stock=stock, available=is_available
    )
    db.add(new_book)
    db.commit()
    
    return RedirectResponse("/", status_code=303)

# --- Mostrar página de edición ---
@router.get("/edit/{book_id}")
def edit_book_page(
    request: Request, 
    book_id: str, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_user_from_cookie)
):
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(request, "edit.html", {"request": request, "book": book, "user": current_user})

# --- Guardar los cambios del libro ---
@router.post("/edit/{book_id}")
def edit_book_logic(
    book_id: str,
    name: str = Form(...),
    author: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    stock: int = Form(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_user_from_cookie)
):
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book:
        book.name = name
        book.author = author
        book.price = price
        book.description = description
        book.stock = stock
        book.available = stock > 0 
        
        db.commit()
        
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)