from fastapi import APIRouter
from app.modules.quotes.controllers import quote_controller

# Main router for quotes module
router = APIRouter()
router.include_router(quote_controller.router, prefix="/quotes", tags=["quotes"])
