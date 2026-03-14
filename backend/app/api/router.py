from fastapi import APIRouter

from app.api.v1 import auth, calendar, elf, events, reviews

router = APIRouter()

router.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
router.include_router(events.router, prefix="/v1/events", tags=["events"])
router.include_router(calendar.router, prefix="/v1/calendar", tags=["calendar"])
router.include_router(reviews.router, prefix="/v1/reviews", tags=["reviews"])
router.include_router(elf.router, prefix="/v1/elf", tags=["elf"])
