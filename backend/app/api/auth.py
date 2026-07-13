from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.register(body.name, body.email, body.password, body.department_id, body.role_id)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(body.refresh_token)


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}
