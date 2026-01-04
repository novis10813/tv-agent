"""
Agentic TV Controller
使用 LangChain + Tool Calling 控制 Android TV
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import command, profiles
from app.services.database import init_db, close_db
from app.services.tv_tools import ALL_TOOLS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup"""
    print("🚀 TV Agent")
    print(f"   LiteLLM: {settings.LITELLM_BASE_URL}")
    print(f"   Model: {settings.LITELLM_MODEL}")
    print(f"   TV: {settings.ANDROID_TV_IP}:{settings.ADB_PORT}")
    print(f"   Tools: {len(ALL_TOOLS)}")
    
    try:
        await init_db()
        print("   ✓ Database connected")
    except Exception as e:
        print(f"   ✗ Database error: {e}")
    
    yield
    
    await close_db()
    print("Shutting down...")


app = FastAPI(
    title="TV Agent",
    description="Control Android TV with natural language",
    lifespan=lifespan
)

# Include routers
app.include_router(command.router, tags=["Command"])
app.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])


@app.get("/health")
async def health():
    from app.services.database import db_pool
    return {
        "status": "ok",
        "tools_count": len(ALL_TOOLS),
        "database": "connected" if db_pool else "disconnected"
    }


@app.get("/tools")
async def list_tools():
    return {"tools": [t.name for t in ALL_TOOLS]}
