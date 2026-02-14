# app/schemas.py
from pydantic import BaseModel
from typing import Optional

class BookBase(BaseModel):
    name: str
    author: str
    description: Optional[str] = None
    price: float
    available: bool = False

class BookCreate(BookBase):
    pass

# Response: Lo que devolvemos al usuario.
class BookResponse(BookBase):
    id: str

    class Config:
        from_attributes = True