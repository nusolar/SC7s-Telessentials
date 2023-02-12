from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import crud, models, schemas
from database import SessionLocal, engine

app = FastAPI()

origins = [
    "http://localhost:3000",
    "localhost:3000",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5501"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
    

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/messages/", response_model=list[schemas.Message])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    messages = crud.get_messages(db, skip=skip, limit=limit)
    return messages

@app.post("/messages/")
def add_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    message = schemas.Message(main_current = message.main_current, mppt1 = message.mppt1, mppt2 = message.mppt2, rpm = message.rpm, lowest_voltage = message.lowest_voltage, highest_temp = message.highest_temp)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message