from fastapi import APIRouter
from app.models.schemas import OrderRequest, OrderResponse
from app.services.trading_service import place_order

router = APIRouter()


@router.post("/", response_model=OrderResponse)
def create_order(order: OrderRequest):
    result = place_order(
        stock_code=order.stock_code,
        quantity=order.quantity,
        action=order.action,
        order_type=order.order_type,
        price=order.price,
    )
    return result


@router.get("/")
def list_orders():
    # TODO: implement order history fetch via Breeze API
    return {"orders": []}
