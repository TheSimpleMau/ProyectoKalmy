import uuid
from sqlalchemy import Column, String, Float, Boolean, Integer
from .database import Base

class Book(Base):
    __tablename__ = "books"

    # CAMBIO AQUÍ:
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String, index=True)
    author = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    available = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

