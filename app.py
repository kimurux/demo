from models import User, RepairRequest, Comment, RoleEnum, StatusEnum, Base
from schemas import (
    UserCreate,
    UserDelete,
    RepairRequestCreate,
    RepairRequestUpdate,
    CommentCreate,
    RepairRequestBase,
    LoginRequest,
    UserBase
)
from utils import get_password_hash, verify_password

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from models import User, RepairRequest, Comment, RoleEnum, StatusEnum, Base
from schemas import (UserCreate, 
                     RepairRequestCreate, 
                     RepairRequestUpdate, 
                     RepairRequestBase,
                     RepairRequestUpdateData, 
                     RepairRequestDelete,
                     CommentCreate, 
                     CommentDelete,
                     CommentUpdate,
                     Comment)

from utils import get_password_hash, verify_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from pydantic import ValidationError
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./repair_service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


# ДБ
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Шифрование
SECRET_KEY = "UwU977"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
sessions = {}

def create_access_token(data: dict):
    to_encode = data.copy()
    if data.get("endless", False):
        to_encode.update({"endless": True})
    else:
        expire = datetime.now() + timedelta(minutes=30)
        to_encode.update({"exp": expire, "endless": False})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
): # User
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/login")
def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    sessions.pop(current_user.id, None)
    return JSONResponse(status_code=200, content={"detail": "Successfully logged out"})



@app.get("/users/")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.ADMIN:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No enough permissions")
    query = db.query(User)
    return query.all()

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/users/")
def update_user(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = data.get("user_id")
    update_data = data.get("update_data")
    if not user_id or update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID and update data are required")
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/")
def delete_user(data: UserDelete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not data.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID is required")
    db_user = db.query(User).filter(User.id == data.id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted successfully"}

@app.get("/users/me")
async def read_users_me(current_user: UserBase = Depends(get_current_user)):
   return UserBase.model_validate(current_user)

@app.post("/repair-requests/")
def create_repair_request(data: RepairRequestBase, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_request = RepairRequest(**data.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@app.get("/repair-requests/")
def get_repair_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[StatusEnum] = None
):
    query = db.query(RepairRequest)
    if status:
        query = query.filter(RepairRequest.status == status)
    if current_user.role == RoleEnum.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No enough permissions")
    return query.all()

@app.put("/repair-requests/")
def update_repair_request(
    data: RepairRequestUpdate,
    db: Session = Depends(get_db)
):
    if not getattr(StatusEnum,data.update_data.get("status",None),None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status value: {data.update_data['status']}. Must be a valid StatusEnum value."
        )
    
    if not data.request_id or not data.update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request ID and update data are required"
        )
    
    db_request = db.query(RepairRequest).filter(RepairRequest.id == data.request_id).first()
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    for field, value in data.update_data.items():
        setattr(db_request, field, value)
    
    db.commit()
    db.refresh(db_request)
    return db_request


@app.delete("/repair-requests/")
def delete_repair_request(
    data: RepairRequestDelete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if not data.request_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request ID is required")
    db_request = db.query(RepairRequest).filter(RepairRequest.id == data.request_id).first()
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    db.delete(db_request)
    db.commit()
    return {"detail": "Repair request deleted successfully"}

@app.put("/repair-requests/comments/")
def get_comments(data: CommentUpdate,
    db: Session = Depends(get_db), 
                 current_user: User = Depends(get_current_user)):
    db_request = db.query(RepairRequest).filter(RepairRequest.id == data.id).first()
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    comments = db.query(Comment).all()
    if not comments:
        return {"detail": "No comments found for this request"}
    
    return comments

@app.post("/repair-requests/comments/")
def add_comment(data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    request_id = data.get("request_id")
    text = data.get("text")
    if not request_id or not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request ID and comment text are required")
    db_request = db.query(RepairRequest).filter(RepairRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    db_comment = Comment(
        repair_request_id=request_id,
        user_id=current_user.id,
        text=text,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@app.delete("/repair-requests/comments/")
def delete_comment(data: CommentDelete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment_id = data.get("comment_id")
    if not comment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment ID is required")
    
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if db_comment.user_id != current_user.id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    db.delete(db_comment)
    db.commit()
    return {"detail": f"Comment with ID {comment_id} has been deleted"}

@app.post("/repair-requests/statistics/")
def get_statistics(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.MASTER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    start_date = data.get("start_date",None)
    end_date = data.get("end_date",None)
    query = db.query(RepairRequest)
    if start_date:
        query = query.filter(RepairRequest.created_at >= start_date)
    if end_date:
        query = query.filter(RepairRequest.created_at <= end_date)
    else: pass
    total_requests = query.count()
    completed_requests = query.filter(RepairRequest.status == StatusEnum.COMPLETED).count()
    return {"total_requests": total_requests, "completed_requests": completed_requests}
