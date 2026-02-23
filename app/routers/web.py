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
    """
    Dependencia que extrae y valida el token JWT almacenado en las cookies del navegador.
    Si el token es válido, retorna el objeto del usuario logueado. Si no existe o es inválido, retorna None.
    """
    if not access_token: return None
    try:
        token_limpio = access_token.replace("Bearer ", "")
        payload = jwt.decode(token_limpio, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username = payload.get("sub")
        return db.query(models.User).filter(models.User.username == username).first()
    except:
        return None

# --- Login ---
@router.get("/login", 
            summary="Mostrar página de login", 
            response_description="Vista HTML del formulario de inicio de sesión")
def login_page(request: Request):
    """
    Renderiza la plantilla HTML para el inicio de sesión de usuarios en la plataforma web.
    """
    return templates.TemplateResponse(request, "login.html", {"request": request})

@router.post("/login", 
            summary="Procesar credenciales web",
            responses={
                302: {"description": "Redirección a la página principal tras un login exitoso con la cookie configurada"},
                200: {"description": "Renderiza nuevamente la vista de login con un mensaje de error si las credenciales fallan"}
            })
def login_logic(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    """
    Procesa el formulario web de inicio de sesión.
    Verifica las credenciales del usuario y, si son correctas, genera un token JWT.
    """
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
@router.get("/logout", 
            summary="Cerrar sesión",
            responses={
                302: {"description": "Redirección a la página de login tras borrar la cookie"}
            })
def logout():
    """
    Cierra la sesión del usuario actual eliminando la cookie de su navegador y redirigiéndolo al inicio de sesión.
    """
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# --- Home ---
@router.get("/", 
            summary="Página principal (Catálogo)",
            response_description="Vista HTML con la lista de libros disponibles paginada")
def home(
    request: Request, 
    db: Session = Depends(database.get_db), 
    user = Depends(get_user_from_cookie),
    page: int = Query(1, ge=1),
    search: str | None = Query(None)
):
    """
    Renderiza la página principal mostrando el catálogo de libros.
    Implementa paginación automática limitando los resultados a 6 libros por página. 
    Requiere que el usuario tenga una sesión activa en sus cookies; de lo contrario, lo redirige al login.
    """
    if not user: return RedirectResponse("/login")
    LIMIT = 6
    offset = (page - 1) * LIMIT

    # 1. Iniciamos la consulta base
    query = db.query(models.Item)
    
    # 2. Si el usuario escribió algo, le aplicamos el filtro a LA MISMA consulta
    if search:
        query = query.filter(models.Item.name.ilike(f"%{search}%"))
    
    # 3. Contamos los items usando nuestra consulta ya filtrada (¡muy importante!)
    total_items = query.count()
    total_pages = math.ceil(total_items / LIMIT) if total_items > 0 else 1
    
    # 4. Traemos los resultados usando nuestra consulta ya filtrada
    items = query.offset(offset).limit(LIMIT).all()
    
    return templates.TemplateResponse(request, "index.html", {
        "request": request, 
        "items": items,
        "title": "Librería Chida",
        "user": user,
        "page": page,
        "total_pages": total_pages,
        "search": search
    })

@router.post("/buy/{item_id}", 
            summary="Simular compra de un libro",
            responses={
                303: {"description": "Redirección a la página principal tras procesar la compra o si no hay sesión"}
            })
def buy_item(
    item_id: str, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_user_from_cookie)
):
    """
    Procesa la compra de un libro desde la interfaz web.
    Reduce el stock del libro en 1. Si el stock llega a 0, cambia automáticamente su disponibilidad a False (agotado). 
    Finalmente, redirige al usuario de vuelta a la página principal.
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    
    if db_item and db_item.stock > 0 and db_item.available:
        db_item.stock -= 1
        
        if db_item.stock == 0:
            db_item.available = False
            
        db.commit()
        db.refresh(db_item)

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# --- Aciones de Admin --- 
# --- Borrar libro ---
@router.delete("/delete/items/{item_id}", 
            summary="Eliminar libro (Admin) vía Web",
            responses={
                200: {"description": "Libro eliminado correctamente"},
                403: {"description": "No tienes permisos de administrador"},
                404: {"description": "Libro no encontrado"}
            })
def delete_item_web(item_id: str, db: Session = Depends(database.get_db), user = Depends(get_user_from_cookie)):
    """
    Elimina un libro desde la interfaz web.
    """
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador")
    
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Libro eliminado"})
        
    return JSONResponse(status_code=404, content={"message": "Libro no encontrado"})

# --- Crear libro ---
@router.post("/create", 
            summary="Crear un nuevo libro (Admin)",
            responses={
                303: {"description": "Redirección al Home tras crear el libro"},
                403: {"description": "Imposible realizar acción. Permisos insuficientes."}
            })
def create_item_web(
    name: str = Form(...),
    author: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    stock: int = Form(...),
    db: Session = Depends(database.get_db), 
    user = Depends(get_user_from_cookie)
):
    """
    Procesa el formulario web para agregar un nuevo libro al catálogo.
    Calcula automáticamente si el libro está disponible basándose en si el stock inicial es mayor a 0.
    **Nota:** Requiere rol de 'admin'.
    """
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")

    is_available = stock > 0

    new_item = models.Item(
        name=name, author=author, price=price, 
        description=description, stock=stock, available=is_available
    )
    db.add(new_item)
    db.commit()
    
    return RedirectResponse("/", status_code=303)

# --- Mostrar página de edición ---
@router.get("/edit/{item_id}", 
            summary="Mostrar formulario de edición (Admin)",
            response_description="Vista HTML del formulario precargado con los datos del libro",
            responses={
                303: {"description": "Redirección al Home si no es admin o si el libro no existe"}
            })
def edit_item_page(
    request: Request, 
    item_id: str, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_user_from_cookie)
):
    """
    Renderiza la vista HTML para editar la información de un libro específico.
    Verifica que el usuario sea administrador y que el libro exista antes de mostrar el formulario.
    """
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(request, "edit.html", {"request": request, "item": item, "user": current_user})

# --- Guardar los cambios del libro ---
@router.post("/edit/{item_id}", 
            summary="Guardar edición de libro (Admin)",
            responses={
                303: {"description": "Redirección al Home tras actualizar el libro o si fallan los permisos"}
            })
def edit_item_logic(
    item_id: str,
    name: str = Form(...),
    author: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    stock: int = Form(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_user_from_cookie)
):
    """
    Procesa el formulario web para actualizar los datos de un libro existente.
    Actualiza todos los campos y recalcula la disponibilidad basada en el nuevo stock ingresado.
    **Nota:** Requiere rol de 'admin'. Al finalizar, redirige a la página principal.
    """
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item:
        item.name = name
        item.author = author
        item.price = price
        item.description = description
        item.stock = stock
        item.available = stock > 0 
        
        db.commit()
        
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)