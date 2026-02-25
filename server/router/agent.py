from fastapi import APIRouter

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)

@router.get("/")
async def root():
    return "Hello, Agent!"
