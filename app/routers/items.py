# app/routers/items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, auth

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

# --- Públicas ---

@router.get("",
            response_model=List[schemas.ItemResponse],
            summary="Obtener todos los libros",
            response_description="Lista de libros disponibles")
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    """
    Recupera una lista paginada de todos los libros en el inventario.
    """
    items = db.query(models.Item).offset(skip).limit(limit).all()
    return items

@router.get("/{item_id}",
            response_model=schemas.ItemResponse, 
            summary="Obtener un libro por ID",
            responses={
                404: {"description": "Libro no encontrado"}
            })
def read_item(item_id: str, db: Session = Depends(database.get_db)):
    """
    Busca un libro específico utilizando su identificador único (UUID).
    """
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return item

# --- Protegidas ---

@router.post("",
            response_model=schemas.ItemResponse, 
            status_code=status.HTTP_201_CREATED,
            summary="Crear un nuevo libro",
            response_description="El libro recién creado",
            responses={
                403: {"description": "Imposible realizar acción. Permisos insuficientes."}
            })
def create_item(
    item: schemas.ItemCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Crea un nuevo registro de libro en el inventario.
    **Nota:** Esta acción requiere que el usuario tenga rol de administrador.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")
    
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{item_id}", 
            response_model=schemas.ItemResponse,
            summary="Actualizar un libro existente",
            response_description="El libro actualizado con los nuevos datos",
            responses={
                403: {"description": "Imposible realizar acción."},
                404: {"description": "Libro no encontrado"}
            })
def update_item(
    item_id: str, 
    item_update: schemas.ItemCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Modifica la información de un libro existente buscando por su ID.
    Reemplaza los datos actuales del libro con los proporcionados en la petición. 
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    for key, value in item_update.model_dump().items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}", 
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Eliminar un libro",
            responses={
                403: {"description": "Imposible realizar acción. Permisos insuficientes."},
                404: {"description": "Libro no encontrado"}
            })
def delete_item(
    item_id: str, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Elimina un libro del inventario de forma permanente utilizando su identificador único (ID).
    **Nota:** Requiere privilegios de administrador. Una vez eliminado, no retornará ningún contenido (204 No Content).
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")

    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    db.delete(db_item)
    db.commit()
    return None