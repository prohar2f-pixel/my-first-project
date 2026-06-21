from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    credits = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    prompt = Column(String, nullable=False)
    negative_prompt = Column(String, default="")
    settings = Column(JSON, default={})
    image_urls = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
