"""Pydantic request/response schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DetectionResult(BaseModel):
    """Face detection result."""
    x: int = Field(..., ge=0, description="Left edge in pixels")
    y: int = Field(..., ge=0, description="Top edge in pixels")
    width: int = Field(..., gt=0, description="ROI width in pixels")
    height: int = Field(..., gt=0, description="ROI height in pixels")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence")
    frame_width: int = Field(..., gt=0, description="Original frame width")
    frame_height: int = Field(..., gt=0, description="Original frame height")


class IngestResponse(BaseModel):
    """Response from frame ingestion endpoint."""
    frame_id: UUID
    roi: Optional[DetectionResult] = None
    message: str = "Frame processed successfully"


class ROIRecordResponse(BaseModel):
    """ROI record response schema."""
    id: UUID
    session_id: UUID
    frame_seq: int
    captured_at: datetime
    x: int
    y: int
    width: int
    height: int
    confidence: Optional[float]
    frame_w: int
    frame_h: int
    has_face: bool
    
    class Config:
        from_attributes = True


class ROIQueryParams(BaseModel):
    """Query parameters for ROI history endpoint."""
    limit: int = Field(default=50, ge=1, le=1000, description="Max records to return")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    session_id: Optional[UUID] = Field(default=None, description="Filter by session ID")
    since: Optional[datetime] = Field(default=None, description="Filter by timestamp")
    
    @field_validator("since", mode="before")
    @classmethod
    def parse_since(cls, v):
        """Parse ISO8601 timestamp string."""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            from datetime import datetime
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class ROIListResponse(BaseModel):
    """Paginated ROI list response."""
    total: int
    offset: int
    limit: int
    items: list[ROIRecordResponse]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    db: bool
    detector: bool
