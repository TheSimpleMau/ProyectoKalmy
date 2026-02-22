# app/routers/books.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, auth

router = APIRouter(
    prefix="/books",
    tags=["books"]
)

# --- Públicas ---

@router.get("/", response_model=List[schemas.BookResponse])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    books = db.query(models.Book).offset(skip).limit(limit).all()
    return books

@router.get("/{book_id}", response_model=schemas.BookResponse)
def read_book(book_id: str, db: Session = Depends(database.get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return book

# --- Protegidas ---

@router.post("/", response_model=schemas.BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book: schemas.BookCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")
    
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.put("/{book_id}", response_model=schemas.BookResponse)
def update_book(
    book_id: str, 
    book_update: schemas.BookCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
    for key, value in book_update.model_dump().items():
        setattr(db_book, key, value)
    
    db.commit()
    db.refresh(db_book)
    return db_book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: str, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Imposible realizar acción.")

    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    db.delete(db_book)
    db.commit()
    return None