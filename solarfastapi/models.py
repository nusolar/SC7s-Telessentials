# coding: utf-8
from sqlalchemy import Column, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    main_current = Column(Float)
    mppt1 = Column(Float)
    mppt2 = Column(Float)
    rpm = Column(Float)
    lowest_voltage = Column(Float)
    highest_temp = Column(Float)