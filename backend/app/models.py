"""SQLAlchemy ORM models."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, BigInteger, Integer, Float, Index, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ROIRecord(Base):
    """ROI (Region of Interest) detection record."""
    
    __tablename__ = "roi_records"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Session tracking
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    frame_seq: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Timestamp
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    # Bounding box coordinates
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Detection metadata
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Frame dimensions
    frame_w: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_h: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Detection status
    has_face: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Index for efficient querying
    __table_args__ = (
        Index("idx_roi_session", "session_id", "captured_at"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ROIRecord(id={self.id}, session_id={self.session_id}, "
            f"has_face={self.has_face}, confidence={self.confidence})>"
        )
