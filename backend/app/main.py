import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import engine, Base
from app.scheduler import start_scheduler, shutdown_scheduler, scheduler
from app.routers import research, emails, followups, replies, influencers, dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Influencer Outreach Automation Backend...")
    try:
        start_scheduler()
    except Exception as e:
        logger.error("Failed to start scheduler: %s", e)
    yield
    logger.info("Shutting down background services...")
    try:
        shutdown_scheduler()
    except Exception as e:
        logger.error("Error shutting down scheduler: %s", e)


app = FastAPI(
    title="AI Instagram Influencer Outreach Automation API",
    description="Automated CRM backend with Instagram Discovery, Claude Filtering, Gmail Outreach, Follow-ups & Reply Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "error": str(exc)}
    )


# Health route
@app.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Instagram Influencer Outreach Automation",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "scheduler_active": scheduler.running if scheduler else False,
        "daily_send_limit": settings.DAILY_SEND_LIMIT,
        "integrations": {
            "instagram_api": bool(settings.INSTAGRAM_ACCESS_TOKEN and settings.INSTAGRAM_BUSINESS_ACCOUNT_ID),
            "anthropic_claude": bool(settings.ANTHROPIC_API_KEY),
            "google_sheets": bool(settings.GOOGLE_SERVICE_ACCOUNT_FILE),
            "gmail_api": bool(settings.GMAIL_TOKEN_FILE)
        }
    }


# Include Routers
app.include_router(research.router)
app.include_router(emails.router)
app.include_router(followups.router)
app.include_router(replies.router)
app.include_router(influencers.router)
app.include_router(dashboard.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
