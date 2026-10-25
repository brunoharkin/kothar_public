
from fastapi import APIRouter
from .system_routes import router as system_router
from .project_tools_api import router as tools_router
from .chat_proxy import router as chat_router

router = APIRouter()
router.include_router(system_router)
router.include_router(tools_router)
router.include_router(chat_router)
