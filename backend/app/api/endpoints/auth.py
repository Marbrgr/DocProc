from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
async def register():
    return {"message": "User registered successfully"}