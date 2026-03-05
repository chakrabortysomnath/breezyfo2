from fastapi import APIRouter, HTTPException
from app.models.schemas import OptionChainRequest, QuoteRequest, QuoteResponse
from app.services.trading_service import get_option_chain, get_quote
from app.services.breeze_service import reset_breeze_client

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
    try:
        raw = get_quote(
            stock_code=req.stock_code,
            exchange_code=req.exchange_code,
            product_type=req.product_type,
            expiry_date=req.expiry_date or "",
            right=req.right or "",
            strike_price=req.strike_price or 0,
        )
    except Exception as exc:
        # Session may have expired — drop the singleton so the next request
        # re-authenticates, then surface the error to the caller.
        reset_breeze_client()
        raise HTTPException(status_code=502, detail=f"Breeze API error: {exc}")
    # Breeze returns {"Status": 200, "Error": None, "Success": [...]}
    # Errors are also returned as HTTP 200 with a non-200 Status field.
    if raw.get("Status") != 200 or raw.get("Error"):
        reset_breeze_client()
        raise HTTPException(
            status_code=502,
            detail=f"Breeze error: {raw.get('Error') or 'unknown error'}",
        )
    success = raw.get("Success") or []
    data = success[0] if success else {}
    # Breeze cash-equity response has no "close" key — only "previous_close".
    # Use explicit None checks so that a legitimate 0.0 value is not dropped
    # by Python's falsy `or` short-circuit.
    ltp_raw = data.get("ltp")
    ltp = _f(ltp_raw if ltp_raw is not None else data.get("last_rate"))

    close_raw = data.get("close")
    close = _f(close_raw if close_raw is not None else data.get("previous_close"))

    vol_raw = data.get("total_quantity_traded")
    volume = _i(vol_raw if vol_raw is not None else data.get("volume"))

    return QuoteResponse(
        stock_code=req.stock_code,
        exchange_code=req.exchange_code,
        ltp=ltp,
        open=_f(data.get("open")),
        high=_f(data.get("high")),
        low=_f(data.get("low")),
        close=close,
        volume=volume,
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
