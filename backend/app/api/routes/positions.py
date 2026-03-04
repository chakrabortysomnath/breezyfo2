from fastapi import APIRouter
from app.services.trading_service import get_portfolio_positions

router = APIRouter()


@router.get("/")
def get_positions():
    result = get_portfolio_positions()
    return result
