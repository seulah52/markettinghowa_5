from fastapi import APIRouter
from app.api.v1.endpoints import analysis, branding, marketing, wanghong, chatbot

router = APIRouter()
router.include_router(analysis.router,  prefix="/analysis",  tags=["analysis"])
router.include_router(branding.router,  prefix="/branding",  tags=["branding"])
router.include_router(marketing.router, prefix="/marketing", tags=["marketing"])
router.include_router(wanghong.router,  prefix="/wanghong",  tags=["wanghong"])
router.include_router(chatbot.router,   prefix="/chatbot",   tags=["chatbot"])
