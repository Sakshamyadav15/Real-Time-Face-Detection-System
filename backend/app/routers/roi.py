"""ROI history query endpoint."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import ROIRecord
from ..schemas import ROIListResponse, ROIRecordResponse, ROIQueryParams

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["roi"])


@router.get("/roi", response_model=ROIListResponse)
async def get_roi_history(
    limit: int = Query(default=50, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    session_id: Optional[UUID] = Query(default=None, description="Filter by session ID"),
    since: Optional[str] = Query(default=None, description="Filter by ISO8601 timestamp"),
    db: AsyncSession = Depends(get_db)
) -> ROIListResponse:
    """
    Query ROI detection history with pagination and filtering.
    
    Args:
        limit: Maximum number of records to return (1-1000)
        offset: Number of records to skip for pagination
        session_id: Optional filter by session ID
        since: Optional filter by timestamp (ISO8601 format)
        
    Returns:
        Paginated list of ROI records
    """
    # Build query
    query = select(ROIRecord)
    
    # Apply filters
    if session_id is not None:
        query = query.where(ROIRecord.session_id == session_id)
    
    if since is not None:
        # Parse ISO8601 timestamp
        from datetime import datetime
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            query = query.where(ROIRecord.captured_at >= since_dt)
        except ValueError:
            logger.warning(f"Invalid timestamp format: {since}")
    
    # Order by captured_at descending
    query = query.order_by(ROIRecord.captured_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(ROIRecord)
    if session_id is not None:
        count_query = count_query.where(ROIRecord.session_id == session_id)
    if since is not None:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            count_query = count_query.where(ROIRecord.captured_at >= since_dt)
        except ValueError:
            pass
    
    result = await db.execute(count_query)
    total = result.scalar_one()
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Convert to response schema
    items = [ROIRecordResponse.model_validate(record) for record in records]
    
    return ROIListResponse(
        total=total,
        offset=offset,
        limit=limit,
        items=items
    )
