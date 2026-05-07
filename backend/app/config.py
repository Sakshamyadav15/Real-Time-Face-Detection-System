"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str
    
    # Face Detection
    detector_backend: str = "mediapipe"
    
    # Annotation
    roi_box_color: str = "#00FF00"
    roi_box_thickness: int = 3
    
    # Frame Processing
    max_frame_size_mb: int = 2
    broadcast_queue_size: int = 10
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def max_frame_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_frame_size_mb * 1024 * 1024
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def roi_box_color_rgb(self) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = self.roi_box_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# Global settings instance
settings = Settings()
