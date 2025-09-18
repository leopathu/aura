from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import schemas, models, utils, database

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register
@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = utils.hash_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}

# Login
@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = utils.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# Forgot Password (simulation only)
@router.post("/forgot-password")
def forgot_password(req: schemas.ForgotPassword, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == req.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # Normally, send email with tokenized reset link
    return {"msg": f"Password reset link sent to {req.email} (simulated)"}