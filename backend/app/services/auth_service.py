import uuid
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user_model import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def _truncate(password: str) -> str:
    """bcrypt silently truncates at 72 bytes; be explicit to avoid verify mismatches."""
    return password.encode()[:72].decode("utf-8", errors="ignore")


def hash_password(plain: str) -> str:
    return pwd_context.hash(_truncate(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate(plain), hashed)


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    username = decode_token(credentials.credentials)
    user = db.query(User).filter(User.username == username).first()
    if not user or user.status != "approved":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied")
    return user


def register_user(db: Session, username: str, email: str, password: str) -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        status="pending",
        approval_token=str(uuid.uuid4()),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, username: str, password: str) -> str:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="Account pending admin approval")
    if user.status == "rejected":
        raise HTTPException(status_code=403, detail="Account access has been rejected")
    return create_access_token(username)


def approve_user(db: Session, approval_token: str) -> User:
    user = db.query(User).filter(User.approval_token == approval_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid approval token")
    user.status = "approved"
    db.commit()
    db.refresh(user)
    return user


def reject_user(db: Session, approval_token: str) -> User:
    user = db.query(User).filter(User.approval_token == approval_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid approval token")
    user.status = "rejected"
    db.commit()
    db.refresh(user)
    return user
