"""WebSocket broadcaster for streaming annotated frames."""
import asyncio
import logging
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts frames."""
    
    def __init__(self, max_queue_size: int = 10):
        """
        Initialize connection manager.
        
        Args:
            max_queue_size: Maximum queue size per client. Slow clients will drop frames.
        """
        self.active_connections: Set[WebSocket] = set()
        self.client_queues: dict[WebSocket, asyncio.Queue] = {}
        self.max_queue_size = max_queue_size
        self._consumer_tasks: dict[WebSocket, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Create queue for this client
        queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.client_queues[websocket] = queue
        
        # Start consumer task for this client
        task = asyncio.create_task(self._consume_queue(websocket, queue))
        self._consumer_tasks[websocket] = task
        
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to unregister
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Cancel consumer task
        if websocket in self._consumer_tasks:
            task = self._consumer_tasks[websocket]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._consumer_tasks[websocket]
        
        # Clean up queue
        if websocket in self.client_queues:
            del self.client_queues[websocket]
        
        logger.debug(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, data: bytes) -> None:
        """
        Broadcast binary data to all connected clients.
        
        Args:
            data: Binary data to broadcast (typically JPEG bytes)
        """
        if not self.active_connections:
            return
        
        # Put data in each client's queue
        disconnected = []
        for websocket in self.active_connections:
            queue = self.client_queues.get(websocket)
            if queue is None:
                disconnected.append(websocket)
                continue
            
            try:
                # Try to put without blocking
                queue.put_nowait(data)
            except asyncio.QueueFull:
                # Queue is full, drop oldest frame
                try:
                    queue.get_nowait()
                    queue.put_nowait(data)
                    logger.debug(f"Dropped frame for slow client")
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass
        
        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def _consume_queue(self, websocket: WebSocket, queue: asyncio.Queue) -> None:
        """
        Consumer task that sends frames from queue to WebSocket.
        
        Args:
            websocket: WebSocket connection
            queue: Queue containing frames to send
        """
        try:
            while True:
                # Wait for frame from queue
                data = await queue.get()
                
                # Send to client
                try:
                    await websocket.send_bytes(data)
                except Exception as e:
                    logger.error(f"Error sending frame to client: {e}")
                    break
        except asyncio.CancelledError:
            logger.debug("Consumer task cancelled")
        except Exception as e:
            logger.error(f"Consumer task error: {e}")
        finally:
            # Ensure cleanup without re-entering disconnect (task is already ending)
            self.active_connections.discard(websocket)
            self._consumer_tasks.pop(websocket, None)
            self.client_queues.pop(websocket, None)
            logger.debug(f"Consumer task cleaned up. Remaining connections: {len(self.active_connections)}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
