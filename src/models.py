from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tid = Column(BigInteger, unique=True, nullable=False)
    tun = Column(String(50), nullable=True)
    step = Column(String(20), nullable=True)
    ptime = Column(DateTime, nullable=True)
    p = Column(Integer, nullable=True)

#class Event(Base):
#    __tablename__  = 'event'
#
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    end = Column(DateTime, nullable=False)
#
#class Participate(Base):
#    __tablename__ = 'participate'
#
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
#    event_id = Column(Integer, ForeignKey('event.id'), nullable=False)
#    value = Column(Integer, nullable=False)
#
#    user = relationship('User', foreign_keys=[user_id], back_populates='participate')
#    event = relationship('Event', foreign_keys=[event_id], back_populates='participate')
