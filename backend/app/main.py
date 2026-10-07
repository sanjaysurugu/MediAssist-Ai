from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine, ensure_user_avatar_column


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager.
    Initializes database tables on application startup.
    """
    # Create tables automatically if they don't exist
    Base.metadata.create_all(bind=engine)
    ensure_user_avatar_column()
    yield
    # Cleanup on shutdown if required


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    description=(
        "🏥 MediAssist AI: AI-powered healthcare assistance and educational decision-support platform "
        "— not a diagnostic system. Never replaces professional medical consultation."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([
        *settings.BACKEND_CORS_ORIGINS,
        settings.frontend_url,
    ])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "online",
        "medical_disclaimer": (
            "IMPORTANT NOTICE: MediAssist AI is an educational decision-support platform, "
            "not a diagnostic system. It does not replace professional medical advice, "
            "diagnosis, or treatment. In case of emergency, call local emergency services immediately."
        )
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
