from typing import TypeVar

from sqlalchemy import Column, String, LargeBinary

from sqlalchemy.ext.declarative import declarative_base

VT = TypeVar("VT")

Base = declarative_base()


class Content(Base):
    __tablename__ = "content"
    id = Column(String(40), primary_key=True)
    blob = Column(LargeBinary(length=(2**32) - 1))
