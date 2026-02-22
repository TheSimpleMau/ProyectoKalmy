# app/schemas.py
from pydantic import BaseModel
from typing import Optional

# --- BOOKS ---

class BookBase(BaseModel):
    name: str
    author: str
    description: Optional[str] = None
    price: float
    available: bool = False
    stock: int = 0

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: str

    class Config:
        from_attributes = True

# --- USER ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

# --- TOKEN ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None