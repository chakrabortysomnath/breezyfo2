from app.services.breeze_service import get_breeze_client


def get_portfolio_positions():
    breeze = get_breeze_client()
    return breeze.get_portfolio_positions()


def place_order(stock_code: str, quantity: int, action: str, order_type: str, price: float = 0):
    breeze = get_breeze_client()
    return breeze.place_order(
        stock_code=stock_code,
        quantity=quantity,
        action=action,
        order_type=order_type,
        price=price,
        exchange_code="NFO",
        product="options",
    )


def get_option_chain(stock_code: str, expiry_date: str, option_type: str):
    breeze = get_breeze_client()
    return breeze.get_option_chain_quotes(
        stock_code=stock_code,
        exchange_code="NFO",
        expiry_date=expiry_date,
        option_type=option_type,
    )
