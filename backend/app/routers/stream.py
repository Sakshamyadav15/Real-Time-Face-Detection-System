"""WebSocket streaming endpoint."""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.broadcaster import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stream"])

# Global broadcaster instance (initialized in main.py lifespan)
broadcaster: ConnectionManager = None


def set_broadcaster(bc: ConnectionManager):
    """Set global broadcaster instance."""
    global broadcaster
    broadcaster = bc


@router.websocket("/ws/stream")
async def stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming annotated frames.
    
    Clients connect to this endpoint to receive real-time annotated video frames
    as binary JPEG data.
    """
    if broadcaster is None:
        logger.error("Broadcaster not initialized")
        await websocket.close(code=1011, reason="Service unavailable")
        return
    
    # Register connection
    await broadcaster.connect(websocket)
    
    try:
        # Keep connection alive
        # The broadcaster will send frames via the consumer task
        while True:
            # Wait for client messages (we don't expect any, but need to keep connection alive)
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Unregister connection
        await broadcaster.disconnect(websocket)
