from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models import User
from app.utils.auth import hash_password, verify_password
from app.utils.jwt import create_access_token, get_current_user


router = APIRouter()

# request models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # check if user already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    #check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_pwd,
        documents_processed=0,
        is_admin=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    return {
        "message": "User registered successfully",
        "user_id": str(new_user.id),
        "username": new_user.username
    }


@router.post("/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "username": user.username
    }

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 🆕 NEW: Calculate documents processed dynamically to ensure accuracy
    from app.models import Document
    documents_count = db.query(Document).filter(Document.user_id == current_user.id).count()
    
    # Update the stored count to keep it in sync
    if current_user.documents_processed != documents_count:
        current_user.documents_processed = documents_count
        db.commit()
    
    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "documents_processed": documents_count,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at,
    }

