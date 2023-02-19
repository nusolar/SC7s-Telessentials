from sqlalchemy.orm import Session

import models, schemas

def get_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Message).offset(skip).limit(limit).all()

def create_message(db: Session, message: schemas.MessageCreate):
    db_message = models.Message(
        main_current = message.main_current,
        mppt1 = message.mppt1,
        mppt2 = message.mppt2,
        rpm = message.rpm,
        lowest_voltage = message.lowest_voltage,
        highest_temp = message.highest_temp
    )
    db.add(db_message)
    db.commit()
    #db.refresh(db_message)
    return db_message