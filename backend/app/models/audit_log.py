from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    success = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
