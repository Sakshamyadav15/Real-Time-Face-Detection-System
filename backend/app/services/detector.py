"""Face detection service using MediaPipe, dlib, or scikit-image (NO OpenCV)."""
import io
import logging
from dataclasses import dataclass
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class FaceDetectorUnavailableError(Exception):
    """Raised when no face detector backend is available."""
    pass


@dataclass
class DetectionResult:
    """Face detection result."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    frame_width: int
    frame_height: int


class FaceDetector:
    """Face detector with fallback chain: MediaPipe → dlib → scikit-image."""
    
    def __init__(self, backend: str = "mediapipe"):
        """Initialize detector with specified backend."""
        self.backend = backend
        self.detector = None
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize detector with fallback chain."""
        # Try MediaPipe first
        if self.backend == "mediapipe" or self.backend == "auto":
            try:
                import mediapipe as mp
                self.mp_face_detection = mp.solutions.face_detection
                self.detector = self.mp_face_detection.FaceDetection(
                    model_selection=0,  # 0 for faces within 2m
                    min_detection_confidence=0.5
                )
                self.backend = "mediapipe"
                logger.info("Initialized MediaPipe face detector")
                return
            except ImportError:
                logger.warning("MediaPipe not available, trying dlib")
        
        # Try dlib as fallback
        if self.backend == "dlib" or self.backend == "auto":
            try:
                import dlib
                self.detector = dlib.get_frontal_face_detector()
                self.backend = "dlib"
                logger.info("Initialized dlib face detector")
                return
            except ImportError:
                logger.warning("dlib not available, trying scikit-image")
        
        # Try scikit-image with Haar cascades as last resort
        if self.backend == "skimage" or self.backend == "auto":
            try:
                from skimage.feature import Cascade
                import skimage.data
                # Use built-in Haar cascade
                self.detector = Cascade(skimage.data.lbp_frontal_face_cascade_filename())
                self.backend = "skimage"
                logger.info("Initialized scikit-image face detector")
                return
            except ImportError:
                logger.error("scikit-image not available")
        
        # All backends failed
        raise FaceDetectorUnavailableError(
            "No face detection backend available. Install mediapipe, dlib, or scikit-image."
        )
    
    def detect(self, image_bytes: bytes) -> Optional[DetectionResult]:
        """
        Detect face in image bytes.
        
        Args:
            image_bytes: Raw image bytes (JPEG or PNG)
            
        Returns:
            DetectionResult if face found, None otherwise
        """
        if self.detector is None:
            raise FaceDetectorUnavailableError("Detector not initialized")
        
        # Load image with Pillow
        img = Image.open(io.BytesIO(image_bytes))
        img_rgb = img.convert("RGB")
        frame_width, frame_height = img_rgb.size
        
        if self.backend == "mediapipe":
            return self._detect_mediapipe(img_rgb, frame_width, frame_height)
        elif self.backend == "dlib":
            return self._detect_dlib(img_rgb, frame_width, frame_height)
        elif self.backend == "skimage":
            return self._detect_skimage(img_rgb, frame_width, frame_height)
        
        return None
    
    def _detect_mediapipe(
        self, img: Image.Image, frame_width: int, frame_height: int
    ) -> Optional[DetectionResult]:
        """Detect face using MediaPipe."""
        import numpy as np
        
        # Convert PIL to numpy array
        img_array = np.array(img)
        
        # Validate image array
        if img_array is None or img_array.size == 0:
            logger.warning("Empty image array received")
            return None
        
        # Ensure correct shape and type
        if len(img_array.shape) != 3 or img_array.shape[2] != 3:
            logger.warning(f"Invalid image shape: {img_array.shape}")
            return None
        
        # Ensure uint8 type
        if img_array.dtype != np.uint8:
            img_array = img_array.astype(np.uint8)
        
        try:
            # Run detection
            results = self.detector.process(img_array)
        except Exception as e:
            logger.error(f"MediaPipe processing error: {e}")
            return None
        
        if not results.detections:
            return None
        
        # Get first detection
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        
        # Convert relative coordinates to absolute pixels
        x = int(bbox.xmin * frame_width)
        y = int(bbox.ymin * frame_height)
        width = int(bbox.width * frame_width)
        height = int(bbox.height * frame_height)
        
        # Ensure coordinates are within bounds
        x = max(0, x)
        y = max(0, y)
        width = min(width, frame_width - x)
        height = min(height, frame_height - y)
        
        return DetectionResult(
            x=x,
            y=y,
            width=width,
            height=height,
            confidence=detection.score[0],
            frame_width=frame_width,
            frame_height=frame_height
        )
    
    def _detect_dlib(
        self, img: Image.Image, frame_width: int, frame_height: int
    ) -> Optional[DetectionResult]:
        """Detect face using dlib."""
        import numpy as np
        
        # Convert PIL to numpy array
        img_array = np.array(img)
        
        # Run detection
        detections = self.detector(img_array, 1)
        
        if len(detections) == 0:
            return None
        
        # Get first detection
        d = detections[0]
        
        return DetectionResult(
            x=d.left(),
            y=d.top(),
            width=d.right() - d.left(),
            height=d.bottom() - d.top(),
            confidence=1.0,  # dlib doesn't provide confidence scores
            frame_width=frame_width,
            frame_height=frame_height
        )
    
    def _detect_skimage(
        self, img: Image.Image, frame_width: int, frame_height: int
    ) -> Optional[DetectionResult]:
        """Detect face using scikit-image."""
        import numpy as np
        
        # Convert to grayscale for Haar cascade
        img_gray = img.convert("L")
        img_array = np.array(img_gray)
        
        # Run detection
        detections = self.detector.detect_multi_scale(
            img=img_array,
            scale_factor=1.2,
            step_ratio=1,
            min_size=(60, 60),
            max_size=(500, 500)
        )
        
        if len(detections) == 0:
            return None
        
        # Get first detection
        d = detections[0]
        
        return DetectionResult(
            x=d['c'],
            y=d['r'],
            width=d['width'],
            height=d['height'],
            confidence=1.0,  # scikit-image doesn't provide confidence scores
            frame_width=frame_width,
            frame_height=frame_height
        )
    
    def is_available(self) -> bool:
        """Check if detector is available."""
        return self.detector is not None
