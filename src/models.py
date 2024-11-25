from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tid = Column(BigInteger, unique=True, nullable=False)
    tun = Column(String(50), nullable=True)
    tn = Column(String(70), nullable=False)
    step = Column(String(20), nullable=True)

#class Event(Base):
#    __tablename__  = 'event'
#
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    end = Column(DateTime, nullable=False)
#
class Participate(Base):
    __tablename__ = 'participate'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    # event_id = Column(Integer, ForeignKey('event.id'), nullable=False)
    value = Column(Integer, nullable=False)
    settime = Column(DateTime, nullable=False)
    fortime = Column(DateTime, nullable=False)

    user = relationship('User', foreign_keys=[user_id], backref='participate')
    # event = relationship('Event', foreign_keys=[event_id], back_populates='participate')


class Admin(Base):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tun = Column(String(30), unique=True)