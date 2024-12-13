from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class RoleEnum(str, Enum):
    admin = "admin"
    master = "master"
    client = "client"

class StatusEnum(str, Enum):
    новая_заявка = "новая заявка"
    в_работе = "в работе"
    завершено = "завершено"

class UserBase(BaseModel):
    username: str
    full_name: str
    phone: str
    role: RoleEnum = "client" 

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str

class UserDelete(BaseModel):
    id: int

class User(UserBase):
    id: int

class LoginRequest(BaseModel):
    username: str
    password: str

class StatisticRequest(BaseModel):
    start_date: str
    end_date: str

class RepairRequestBase(BaseModel):
    equipment_type: Optional[str] = None
    model: Optional[str] = None
    problem_description: Optional[str] = None  

class RepairRequestCreate(RepairRequestBase):
    client_id: int

class RepairRequestDelete(BaseModel):
    request_id: int

class RepairRequestUpdate(BaseModel):
    request_id: int
    update_data: dict

class RepairRequestUpdateData(BaseModel):
    status: Optional[StatusEnum] = "новая заявка"
    problem_description: Optional[str]
    master_id: Optional[int]

class RepairRequest(RepairRequestBase):
    id: int
    created_at: datetime
    status: StatusEnum
    client: User
    master: Optional[User]

class CommentCreate(BaseModel):
    text: str
    parts_info: Optional[str]

class CommentDelete(BaseModel):
    id: int

class CommentUpdate(CommentCreate):
    id: int

class Comment(CommentCreate):
    id: int
    created_at: datetime
    user: User
