from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class StatusEnum(str, enum.Enum):
    NEW = "новая заявка"
    IN_PROGRESS = "в процессе ремонта"
    WAITING_PARTS = "ожидание запчастей"
    COMPLETED = "завершена"
    READY = "готова к выдаче"

class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    MASTER = "master"
    CLIENT = "client"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True,autoincrement=True)
    username = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(Enum(RoleEnum))
    full_name = Column(String)
    phone = Column(String)

class RepairRequest(Base):
    __tablename__ = "repair_requests"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    equipment_type = Column(String)
    model = Column(String)
    problem_description = Column(String)
    client_id = Column(Integer, ForeignKey("users.id"))
    master_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.NEW)
    
    client = relationship("User", foreign_keys=[client_id], order_by=id)
    master = relationship("User", foreign_keys=[master_id], order_by=id)
    comments = relationship("Comment", back_populates="repair_request")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True)
    repair_request_id = Column(Integer, ForeignKey("repair_requests.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    text = Column(String)
    parts_info = Column(String, nullable=True)
    
    repair_request = relationship("RepairRequest", back_populates="comments")
    user = relationship("User")