from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    buy = "buy"
    sell = "sell"


class OrderType(str, Enum):
    market = "market"
    limit = "limit"
    stop_loss = "stop_loss"


class OrderRequest(BaseModel):
    stock_code: str
    quantity: int
    action: ActionType
    order_type: OrderType
    price: Optional[float] = 0.0


class OptionChainRequest(BaseModel):
    stock_code: str
    expiry_date: str
    option_type: str  # "call" or "put"


class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str


# Auth schemas
class RegisterRequest(BaseModel):
    username: str
    password: str
    access_code: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
