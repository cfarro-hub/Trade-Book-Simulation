"""
FastAPI application factory v2.1 — FIXED event loop injection.
"""

import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, RATE_LIMIT
from app.database.db import init_db, SessionLocal
from app.engine.matching_engine import MatchingEngine
from app.api import routes_orders, routes_book, routes_trades
from app.api.websocket import ConnectionManager, websocket_endpoint


def create_app() -> FastAPI:
    application = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )

    # Rate limiter
    limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Database
    init_db()

    # WebSocket manager
    ws_manager = ConnectionManager()

    # Matching engine
    engine = MatchingEngine(
        ws_manager=ws_manager,
        db_session_factory=SessionLocal,
    )

    # Inject engine into route modules
    routes_orders.set_engine(engine)
    routes_book.set_engine(engine)
    routes_trades.set_engine(engine)

    # Mount routers
    application.include_router(routes_orders.router)
    application.include_router(routes_book.router)
    application.include_router(routes_trades.router)

    # Market data router (Binance public API proxy)
    from app.api.routes_market_data import router as market_router, set_engine as set_market_engine
    set_market_engine(engine)
    application.include_router(market_router)

    # WebSocket endpoint
    @application.websocket("/ws")
    async def ws_route(websocket: WebSocket):
        await websocket_endpoint(websocket, ws_manager)

    # CRITICAL FIX: pass the asyncio event loop to the engine at startup
    @application.on_event("startup")
    async def on_startup():
        engine.set_event_loop(asyncio.get_running_loop())

    # Serve static files
    application.mount("/static", StaticFiles(directory="static"), name="static")

    # Serve index.html at root
    @application.get("/", include_in_schema=False)
    async def root():
        return FileResponse("static/index.html")

    application.state.engine = engine
    application.state.ws_manager = ws_manager

    return application


app = create_app()
