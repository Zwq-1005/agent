from app.routers.upload import router as upload_router
from app.routers.session import router as session_router
from app.routers.analyze import router as analyze_router
from app.routers.prompts import router as prompts_router

__all__ = ["upload_router", "session_router", "analyze_router", "prompts_router"]
