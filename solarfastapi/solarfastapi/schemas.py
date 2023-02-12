from pydantic import BaseModel


class MessageBase(BaseModel):
    main_current : float
    mppt1 : float
    mppt2 : float
    rpm : float
    lowest_voltage : float
    highest_temp : float


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int

    class Config:
        orm_mode = True
