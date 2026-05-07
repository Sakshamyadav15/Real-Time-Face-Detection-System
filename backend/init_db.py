"""Initialize SQLite database with tables."""
import asyncio
from app.database import engine, Base
# Import models to register them with Base
from app.models import ROIRecord


async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        # Drop all tables (optional, for clean slate)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized successfully!")
    print(f"Tables created: {list(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    asyncio.run(init_db())
