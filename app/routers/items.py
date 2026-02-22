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

@router.get("/", response_model=List[schemas.ItemResponse])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    items = db.query(models.Item).offset(skip).limit(limit).all()
    return items

@router.get("/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id: str, db: Session = Depends(database.get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return item

# --- Protegidas ---

@router.post("/", response_model=schemas.ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: schemas.ItemCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")
    
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(
    item_id: str, 
    item_update: schemas.ItemCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
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

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: str, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")

    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    db.delete(db_item)
    db.commit()
    return None