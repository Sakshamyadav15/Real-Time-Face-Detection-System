"""Image annotation service using Pillow (NO OpenCV)."""
import io
from PIL import Image, ImageDraw

from .detector import DetectionResult


def draw_roi(image_bytes: bytes, result: DetectionResult, color: tuple[int, int, int] = (0, 255, 0), thickness: int = 3) -> bytes:
    """
    Draw bounding box on image using Pillow.
    
    Args:
        image_bytes: Raw image bytes (JPEG or PNG)
        result: Detection result with bounding box coordinates
        color: RGB color tuple for the box outline
        thickness: Line thickness in pixels
        
    Returns:
        Annotated image as JPEG bytes
    """
    # Open image with Pillow
    img = Image.open(io.BytesIO(image_bytes))
    img_rgb = img.convert("RGB")
    
    # Create drawing context
    draw = ImageDraw.Draw(img_rgb)
    
    # Draw rectangle
    # PIL.ImageDraw.rectangle expects [(x0, y0), (x1, y1)]
    x0 = result.x
    y0 = result.y
    x1 = result.x + result.width
    y1 = result.y + result.height
    
    draw.rectangle(
        [(x0, y0), (x1, y1)],
        outline=color,
        width=thickness
    )
    
    # Save to bytes buffer
    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def sanitize_image(image_bytes: bytes) -> bytes:
    """
    Sanitize image by re-encoding through Pillow.
    
    This ensures the image is valid and removes any potential malicious data.
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Re-encoded image as JPEG bytes
    """
    img = Image.open(io.BytesIO(image_bytes))
    img_rgb = img.convert("RGB")
    
    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG", quality=85)
    return buf.getvalue()
