from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import connect_db, close_db
from app.core.logging_config import setup_logging
from app.repos.indexes import create_indexes
from app.infrastructure.sse_manager import SSEManager
from app.api.errors import register_exception_handlers
from app.api.middleware import RequestContextMiddleware, SlowQueryMiddleware
from app.api.ratelimit import RateLimitMiddleware
from app.api.routers import health, stocks, quotes, screener, sse, indicators, watchlist, market, analysis, portfolio, checklist, routine, auth, sector, news


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await connect_db()
    from app.core.database import db
    await create_indexes(db)
    app.state.sse_manager = SSEManager()
    yield
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(SlowQueryMiddleware, threshold_ms=500)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(health.router, prefix="/api")
app.include_router(stocks.router)
app.include_router(quotes.router)
app.include_router(screener.router)
app.include_router(sse.router)
app.include_router(indicators.router)
app.include_router(watchlist.router)
app.include_router(market.router)
app.include_router(analysis.router)
app.include_router(portfolio.router)
app.include_router(checklist.router)
app.include_router(routine.router)
app.include_router(auth.router)
app.include_router(sector.router, prefix="/api")
app.include_router(news.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": settings.APP_NAME, "version": "1.0.0"}
