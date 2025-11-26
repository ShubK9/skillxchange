# backend/routes/teachers.py

from fastapi import APIRouter

router = APIRouter(prefix="/teachers", tags=["teachers"])

# your routes here...
@router.get("/")
async def get_teachers():
    ...

@router.post("/")
async def create_teacher():
    ...

# ... other routes