from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import requests
import hashlib
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()


class Website(Base):
    __tablename__ = "websites"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)


class WebsiteChange(Base):
    __tablename__ = "website_changes"
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, index=True)
    content_hash = Column(String)
    timestamp = Column(DateTime, default=func.now())


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/add-url/")
def add_url(url: str, db: Session = Depends(get_db)):
    db_url = Website(url=url)
    db.add(db_url)
    db.commit()
    return {"message": "URL added successfully"}


@app.get("/urls/")
def read_urls(db: Session = Depends(get_db)):
    urls = db.query(Website).all()
    return urls
