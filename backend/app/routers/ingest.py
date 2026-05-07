"""Frame ingestion endpoint."""
import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models import ROIRecord
from ..schemas import IngestResponse, DetectionResult as DetectionResultSchema
from ..services.detector import FaceDetector, DetectionResult, FaceDetectorUnavailableError
from ..services.annotator import draw_roi, sanitize_image
from ..services.broadcaster import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["video"])

# Global instances (initialized in main.py lifespan)
detector: FaceDetector = None
broadcaster: ConnectionManager = None
executor = None
current_session_id = uuid.uuid4()
frame_counter = 0


def set_detector(det: FaceDetector):
    """Set global detector instance."""
    global detector
    detector = det


def set_broadcaster(bc: ConnectionManager):
    """Set global broadcaster instance."""
    global broadcaster
    broadcaster = bc


def set_executor(ex):
    """Set global thread pool executor."""
    global executor
    executor = ex


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_200_OK)
async def ingest_frame(
    frame: Annotated[UploadFile, File(description="Video frame (JPEG or PNG)")],
    db: AsyncSession = Depends(get_db)
) -> IngestResponse:
    """
    Ingest a video frame for face detection.
    
    Process:
    1. Validate MIME type and size
    2. Run face detection
    3. Annotate frame if face found
    4. Broadcast annotated frame
    5. Persist ROI metadata to database
    
    Returns:
        IngestResponse with frame_id and optional ROI data
    """
    global frame_counter
    
    # Validate MIME type
    if frame.content_type not in ["image/jpeg", "image/png"]:
        logger.warning(f"Invalid MIME type: {frame.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG/PNG accepted"
        )
    
    # Read frame bytes
    frame_bytes = await frame.read()
    
    # Validate size
    if len(frame_bytes) > settings.max_frame_size_bytes:
        logger.warning(f"Frame too large: {len(frame_bytes)} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Frame exceeds {settings.max_frame_size_mb} MB limit"
        )
    
    # Check detector availability
    if detector is None or not detector.is_available():
        logger.error("Face detector not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Face detector not loaded"
        )
    
    # Run face detection in thread pool (blocking operation)
    try:
        loop = asyncio.get_event_loop()
        detection_result: DetectionResult = await loop.run_in_executor(
            executor,
            detector.detect,
            frame_bytes
        )
    except Exception as e:
        logger.error(f"Face detection error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot decode image"
        )
    
    # Increment frame counter
    frame_counter += 1
    
    # Prepare response
    frame_id = uuid.uuid4()
    roi_response = None
    
    # Process based on detection result
    if detection_result is not None:
        # Face detected - annotate frame
        try:
            annotated_bytes = draw_roi(
                frame_bytes,
                detection_result,
                color=settings.roi_box_color_rgb,
                thickness=settings.roi_box_thickness
            )
        except Exception as e:
            logger.error(f"Annotation error: {e}", exc_info=True)
            # Fall back to original frame
            annotated_bytes = sanitize_image(frame_bytes)
        
        # Broadcast annotated frame
        if broadcaster is not None:
            await broadcaster.broadcast(annotated_bytes)
        
        # Persist ROI record
        roi_record = ROIRecord(
            id=frame_id,
            session_id=current_session_id,
            frame_seq=frame_counter,
            x=detection_result.x,
            y=detection_result.y,
            width=detection_result.width,
            height=detection_result.height,
            confidence=detection_result.confidence,
            frame_w=detection_result.frame_width,
            frame_h=detection_result.frame_height,
            has_face=True
        )
        db.add(roi_record)
        await db.commit()
        
        # Prepare response
        roi_response = DetectionResultSchema(
            x=detection_result.x,
            y=detection_result.y,
            width=detection_result.width,
            height=detection_result.height,
            confidence=detection_result.confidence,
            frame_width=detection_result.frame_width,
            frame_height=detection_result.frame_height
        )
        
        logger.debug(f"Face detected in frame {frame_counter}")
    else:
        # No face detected - broadcast original frame
        sanitized_bytes = sanitize_image(frame_bytes)
        if broadcaster is not None:
            await broadcaster.broadcast(sanitized_bytes)
        
        # Persist record with has_face=False
        # Get frame dimensions
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(frame_bytes))
        frame_w, frame_h = img.size
        
        roi_record = ROIRecord(
            id=frame_id,
            session_id=current_session_id,
            frame_seq=frame_counter,
            x=0,
            y=0,
            width=0,
            height=0,
            confidence=None,
            frame_w=frame_w,
            frame_h=frame_h,
            has_face=False
        )
        db.add(roi_record)
        await db.commit()
        
        logger.debug(f"No face in frame {frame_counter}")
    
    return IngestResponse(
        frame_id=frame_id,
        roi=roi_response,
        message="Frame processed successfully"
    )
