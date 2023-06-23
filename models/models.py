from sqlalchemy import Column, TIMESTAMP, VARCHAR, Integer, Boolean, Text, ForeignKey, CHAR, BigInteger, SmallInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)


class Event(Base):
    __tablename__: str = "events"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    date_event = Column(Text)
    time_event = Column(Text)
    place = Column(Text, nullable=False)
    link = Column(Text, nullable=False)


