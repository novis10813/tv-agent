"""
Database service using asyncpg
"""

import asyncpg
from app.config import settings

db_pool: asyncpg.Pool | None = None


async def init_db():
    """Initialize database and create tables"""
    global db_pool
    db_pool = await asyncpg.create_pool(settings.DATABASE_URL)
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) UNIQUE NOT NULL,
                netflix_profile_index INT DEFAULT 1,
                netflix_pin VARCHAR(10),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)


async def close_db():
    """Close database pool"""
    global db_pool
    if db_pool:
        await db_pool.close()


async def get_user_profile(user_id: str) -> dict | None:
    """Get user profile from database"""
    if not db_pool:
        return None
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1", user_id
        )
        if row:
            return dict(row)
    return None
