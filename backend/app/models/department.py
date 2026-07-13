from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    users = relationship("User", back_populates="department")
    documents = relationship("Document", back_populates="department")
