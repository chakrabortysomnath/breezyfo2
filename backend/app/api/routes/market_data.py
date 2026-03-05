from fastapi import APIRouter
from app.models.schemas import OptionChainRequest, QuoteRequest, QuoteResponse
from app.services.trading_service import get_option_chain, get_quote

router = APIRouter()


@router.post("/option-chain")
def option_chain(req: OptionChainRequest):
    result = get_option_chain(
        stock_code=req.stock_code,
        expiry_date=req.expiry_date,
        option_type=req.option_type,
    )
    return result


@router.post("/quote", response_model=QuoteResponse)
def quote(req: QuoteRequest):
    raw = get_quote(
        stock_code=req.stock_code,
        exchange_code=req.exchange_code,
        product_type=req.product_type,
        expiry_date=req.expiry_date or "",
        right=req.right or "",
        strike_price=req.strike_price or 0,
    )
    # Breeze returns {"Status": 200, "Error": None, "Success": [...]}
    success = raw.get("Success") or []
    data = success[0] if success else {}
    return QuoteResponse(
        stock_code=req.stock_code,
        exchange_code=req.exchange_code,
        ltp=_f(data.get("ltp") or data.get("last_rate")),
        open=_f(data.get("open")),
        high=_f(data.get("high")),
        low=_f(data.get("low")),
        close=_f(data.get("close") or data.get("previous_close")),
        volume=_i(data.get("total_quantity_traded") or data.get("volume")),
        open_interest=_i(data.get("open_interest")),
        raw=data,
    )


def _f(v) -> float | None:
    try:
        return float(v) if v not in (None, "", "0") else None
    except (TypeError, ValueError):
        return None


def _i(v) -> int | None:
    try:
        return int(float(v)) if v not in (None, "", "0") else None
    except (TypeError, ValueError):
        return None
