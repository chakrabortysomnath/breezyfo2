from fastapi import APIRouter
from app.models.schemas import OptionChainRequest
from app.services.trading_service import get_option_chain

router = APIRouter()


@router.post("/option-chain")
def option_chain(req: OptionChainRequest):
    result = get_option_chain(
        stock_code=req.stock_code,
        expiry_date=req.expiry_date,
        option_type=req.option_type,
    )
    return result
