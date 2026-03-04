from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends

from app.api.routes import market_data, orders, positions
from app.api.routes import auth
from app.db import Base, engine
from app.models import user_model  # noqa: F401 — registers User with Base before create_all
from app.services.auth_service import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="F&O Trading API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public — no auth required
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Protected — valid JWT required for all routes in these routers
app.include_router(
    orders.router,
    prefix="/api/orders",
    tags=["Orders"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    positions.router,
    prefix="/api/positions",
    tags=["Positions"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    market_data.router,
    prefix="/api/market",
    tags=["Market Data"],
    dependencies=[Depends(get_current_user)],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
