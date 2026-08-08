from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.repositories.auth import AuthRepository
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.auth_repo = AuthRepository(db)
        self.db = db

    async def register(self, name: str, email: str, password: str, department_id: int, role_id: int = 3) -> dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = await self.user_repo.create(
            name=name,
            email=email,
            password_hash=hash_password(password),
            department_id=department_id,
            role_id=role_id,
        )
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        jti = payload.get("jti")
        if jti and await self.auth_repo.is_blacklisted(jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

        user_id = payload.get("sub")
        user = await self.user_repo.get(int(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if jti:
            await self.auth_repo.blacklist_token(jti)

        access_token = create_access_token({"sub": str(user.id)})
        new_refresh_token = create_refresh_token({"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

    async def logout(self, access_token: str, refresh_token: str) -> dict:
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        access_jti = access_payload.get("jti") if access_payload else None
        refresh_jti = refresh_payload.get("jti") if refresh_payload else None

        if access_jti:
            await self.auth_repo.blacklist_token(access_jti)
        if refresh_jti:
            await self.auth_repo.blacklist_token(refresh_jti)

        return {"message": "Logged out successfully"}
