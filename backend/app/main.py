from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import orders, positions, market_data

app = FastAPI(title="F&O Trading API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
app.include_router(market_data.router, prefix="/api/market", tags=["Market Data"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
