# Face Detection Video Streaming System

A real-time face detection and video streaming system that captures webcam frames, detects faces using MediaPipe, annotates frames with bounding boxes, and streams results to connected clients via WebSocket. All detection metadata is persisted to PostgreSQL for historical analysis.

## Architecture

The system consists of four Docker containers orchestrated via Docker Compose:

**Frontend (React + Nginx)**: Serves the web interface on port 3000. Captures webcam frames at 15 FPS using the MediaStream API, encodes them as JPEG, and POSTs to the backend ingest endpoint. Simultaneously maintains a WebSocket connection to receive and display annotated frames in real-time. Polls the ROI history endpoint to display detection statistics.

**Backend (FastAPI + Python 3.12)**: Exposes REST and WebSocket endpoints on port 8000. Receives raw frames via POST, runs face detection using MediaPipe, draws bounding boxes using Pillow, broadcasts annotated frames to all WebSocket subscribers, and persists ROI metadata to PostgreSQL. All operations are async using asyncio and SQLAlchemy async.

**Database (PostgreSQL 15)**: Stores ROI detection records with bounding box coordinates, confidence scores, timestamps, and session tracking. Runs on an internal Docker network with no host exposure.

**Data Flow**: Browser captures frame → POST to `/api/video/ingest` → Backend detects face → Backend annotates with Pillow → Backend broadcasts via WebSocket → Frontend displays stream → Backend persists metadata to PostgreSQL → Frontend polls `/api/roi` for history.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18, Vite | Web interface and webcam capture |
| Backend | FastAPI, Python 3.12, Uvicorn | Async REST and WebSocket API |
| Face Detection | MediaPipe 0.10.14 | Primary face detection engine |
| Image Processing | Pillow 10.3.0 | Bounding box annotation and image encoding |
| Database | PostgreSQL 15, SQLAlchemy 2 async | ROI metadata persistence |
| Migrations | Alembic 1.13.1 | Database schema versioning |
| Validation | Pydantic 2.7.1 | Request/response schema validation |
| Containerization | Docker Compose v2 | Multi-container orchestration |

## Prerequisites

- Docker Engine 24+
- Docker Compose v2

## Getting Started

```bash
git clone https://github.com/yourusername/face-detection-stream.git
cd face-detection-stream
cp .env.example .env
docker compose up --build
```

Open http://localhost:3000 and allow camera access when prompted.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PASSWORD` | `changeme_in_prod` | PostgreSQL password for user `face` |
| `DETECTOR_BACKEND` | `mediapipe` | Face detection backend: `mediapipe`, `dlib`, or `skimage` |
| `ROI_BOX_COLOR` | `#00FF00` | Bounding box color in hex format |
| `ROI_BOX_THICKNESS` | `3` | Bounding box line thickness in pixels |
| `MAX_FRAME_SIZE_MB` | `2` | Maximum frame size accepted by ingest endpoint |
| `BROADCAST_QUEUE_SIZE` | `10` | WebSocket broadcast queue size per client |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed CORS origins |

## API Reference

### POST /api/video/ingest

Ingest a video frame for face detection and annotation.

**Request**:
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form field `frame` containing JPEG or PNG image (max 2 MB)

**Response** (200 OK):
```json
{
  "frame_id": "550e8400-e29b-41d4-a716-446655440000",
  "roi": {
    "x": 120,
    "y": 80,
    "width": 200,
    "height": 240,
    "confidence": 0.94,
    "frame_width": 640,
    "frame_height": 480
  },
  "message": "Frame processed successfully"
}
```

**Error Responses**:
- `415 Unsupported Media Type`: Invalid MIME type (not JPEG/PNG)
- `413 Request Entity Too Large`: Frame exceeds size limit
- `422 Unprocessable Entity`: Cannot decode image
- `503 Service Unavailable`: Face detector not loaded

### GET /ws/stream

WebSocket endpoint for receiving annotated video frames.

**Protocol**: WebSocket  
**Path**: `/ws/stream`  
**Message Format**: Binary JPEG data  
**Behavior**: Server pushes annotated frames to all connected clients. Slow clients are dropped if their queue fills up.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream');
ws.binaryType = 'arraybuffer';
ws.onmessage = (event) => {
  const blob = new Blob([event.data], { type: 'image/jpeg' });
  const url = URL.createObjectURL(blob);
  // Display image
};
```

### GET /api/roi

Query ROI detection history with pagination and filtering.

**Request**:
- Method: `GET`
- Query Parameters:
  - `limit` (optional, default: 50, range: 1-1000): Maximum records to return
  - `offset` (optional, default: 0): Number of records to skip
  - `session_id` (optional): Filter by session UUID
  - `since` (optional): Filter by ISO8601 timestamp

**Response** (200 OK):
```json
{
  "total": 4821,
  "offset": 0,
  "limit": 50,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "frame_seq": 123,
      "captured_at": "2026-05-07T14:23:45.123456Z",
      "x": 120,
      "y": 80,
      "width": 200,
      "height": 240,
      "confidence": 0.94,
      "frame_w": 640,
      "frame_h": 480,
      "has_face": true
    }
  ]
}
```

### GET /api/health

Health check endpoint for monitoring.

**Request**:
- Method: `GET`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "db": true,
  "detector": true
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Database or detector unavailable

## Database Schema

### roi_records Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique record identifier |
| `session_id` | UUID | NOT NULL | Webcam session identifier (groups frames from same session) |
| `frame_seq` | BIGINT | NOT NULL | Sequential frame number within session |
| `captured_at` | TIMESTAMPTZ | NOT NULL | Frame capture timestamp (UTC) |
| `x` | INTEGER | NOT NULL | Bounding box left edge in pixels |
| `y` | INTEGER | NOT NULL | Bounding box top edge in pixels |
| `width` | INTEGER | NOT NULL | Bounding box width in pixels |
| `height` | INTEGER | NOT NULL | Bounding box height in pixels |
| `confidence` | REAL | NULL | Detector confidence score (0.0-1.0), null if no face |
| `frame_w` | INTEGER | NOT NULL | Original frame width in pixels |
| `frame_h` | INTEGER | NOT NULL | Original frame height in pixels |
| `has_face` | BOOLEAN | NOT NULL | Whether a face was detected in this frame |

**Indexes**:
- `idx_roi_session` on `(session_id, captured_at DESC)` for efficient session queries

**Notes**:
- When `has_face` is false, `x`, `y`, `width`, `height` are set to 0 and `confidence` is null
- `session_id` is generated on backend startup and persists until restart
- `frame_seq` increments monotonically per session

## Face Detection

### Detection Pipeline

The system uses a fallback chain for face detection:

1. **MediaPipe (Primary)**: Google's MediaPipe Face Detection with model selection 0 (optimized for faces within 2 meters). Provides bounding box coordinates and confidence scores. Runs on CPU with acceptable performance (15+ FPS on modern hardware).

2. **dlib (Fallback)**: HOG-based frontal face detector. Activated if MediaPipe import fails. More CPU-intensive but widely compatible.

3. **scikit-image (Last Resort)**: Haar cascade classifier using LBP features. Activated if both MediaPipe and dlib fail. Lowest accuracy but guaranteed availability.

The backend attempts each detector in order and uses the first available. The active detector is logged on startup.

### Image Processing with Pillow

All image operations use Pillow (PIL) instead of OpenCV:

**Rationale**: OpenCV (cv2) is a large dependency (200+ MB) with complex build requirements and GPL licensing concerns. Pillow is lightweight (10 MB), pure Python-compatible, MIT-licensed, and sufficient for this use case.

**Operations**:
- Image loading: `Image.open(io.BytesIO(bytes))`
- Bounding box drawing: `ImageDraw.rectangle()`
- Color space conversion: `Image.convert("RGB")`
- JPEG encoding: `Image.save(buffer, format="JPEG")`
- Image sanitization: Re-encode through Pillow to strip metadata

**Performance**: Pillow's drawing operations are adequate for real-time annotation at 15 FPS. For higher throughput, consider OpenCV or GPU-accelerated alternatives.

## License

MIT

