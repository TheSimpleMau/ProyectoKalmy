# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

# --- ItemS ---

class ItemBase(BaseModel):
    name: str
    author: str
    description: Optional[str] = None
    price: float
    available: bool = False
    stock: int = 0

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

# --- USER ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# --- TOKEN ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None