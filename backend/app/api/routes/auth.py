from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import approve_user, login_user, register_user, reject_user
from app.services.email_service import send_approval_request

router = APIRouter()


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = register_user(db, payload.username, payload.email, payload.password)
    background_tasks.add_task(send_approval_request, user.username, user.email, user.approval_token)
    return {"message": "Registration successful. Your account is pending admin approval."}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = login_user(db, payload.username, payload.password)
    return TokenResponse(access_token=token, token_type="bearer", username=payload.username)


@router.get("/approve/{token}", response_class=HTMLResponse)
def approve(token: str, db: Session = Depends(get_db)):
    user = approve_user(db, token)
    return HTMLResponse(content=_confirmation_page(
        title="User Approved ✅",
        message=f"<strong>{user.username}</strong> has been approved and can now log in.",
        color="#1da1f2",
    ))


@router.get("/reject/{token}", response_class=HTMLResponse)
def reject(token: str, db: Session = Depends(get_db)):
    user = reject_user(db, token)
    return HTMLResponse(content=_confirmation_page(
        title="User Rejected ❌",
        message=f"<strong>{user.username}</strong> has been rejected and cannot access the system.",
        color="#e0245e",
    ))


def _confirmation_page(title: str, message: str, color: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>{title}</title>
      <style>
        body {{ font-family: Arial, sans-serif; display: flex; justify-content: center;
                align-items: center; height: 100vh; margin: 0; background: #f5f8fa; }}
        .card {{ background: white; border-radius: 12px; padding: 40px 48px;
                 box-shadow: 0 2px 12px rgba(0,0,0,0.1); text-align: center; max-width: 480px; }}
        h1 {{ color: {color}; font-size: 28px; margin-bottom: 16px; }}
        p {{ color: #555; font-size: 16px; line-height: 1.5; }}
        .badge {{ display: inline-block; background: {color}; color: white;
                  padding: 6px 16px; border-radius: 20px; font-size: 13px; margin-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>{title}</h1>
        <p>{message}</p>
        <div class="badge">F&amp;O Trader Admin</div>
      </div>
    </body>
    </html>
    """
