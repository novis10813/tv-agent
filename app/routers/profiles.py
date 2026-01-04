"""
Profiles router - CRUD for user profiles
"""

import asyncpg
from fastapi import APIRouter, HTTPException

from app.schemas.models import ProfileCreate, ProfileResponse
from app.services.database import get_pool, get_user_profile

router = APIRouter()


@router.get("", response_model=list[ProfileResponse])
async def list_profiles():
    """列出所有使用者 profiles"""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, netflix_profile_index, netflix_pin FROM user_profiles")
        return [dict(row) for row in rows]


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """取得單一使用者 profile"""
    profile = await get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{user_id}' not found")
    return profile


@router.post("", response_model=ProfileResponse)
async def create_profile(profile: ProfileCreate):
    """新增使用者 profile"""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO user_profiles (user_id, netflix_profile_index, netflix_pin)
                VALUES ($1, $2, $3)
                """,
                profile.user_id, profile.netflix_profile_index, profile.netflix_pin
            )
            return profile
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail=f"Profile '{profile.user_id}' already exists")


@router.put("/{user_id}", response_model=ProfileResponse)
async def update_profile(user_id: str, profile: ProfileCreate):
    """更新使用者 profile"""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_profiles 
            SET netflix_profile_index = $2, netflix_pin = $3, updated_at = NOW()
            WHERE user_id = $1
            """,
            user_id, profile.netflix_profile_index, profile.netflix_pin
        )
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail=f"Profile '{user_id}' not found")
        return profile


@router.delete("/{user_id}")
async def delete_profile(user_id: str):
    """刪除使用者 profile"""
    pool = get_pool()
    if not pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM user_profiles WHERE user_id = $1", user_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail=f"Profile '{user_id}' not found")
        return {"message": f"Profile '{user_id}' deleted"}
