"""
Configuration Management
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://vulnsphere:prime@localhost:5432/vulnsphere"
    REDIS_URL: str = "redis://localhost:6379"
    TIMESCALE_URL: str = "postgresql://vulnsphere:prime@localhost:5433/timeseries"
    
    # ZKAEDI PRIME Parameters
    FRACTAL_ALPHA: float = 0.618
    ETA: float = 0.4
    GAMMA: float = 0.3
    BETA: float = 0.1
    SIGMA: float = 0.05
    PHI: float = 1.618
    
    # Security Scanners
    TRIVY_PATH: str = "/usr/local/bin/trivy"
    ZAP_API_KEY: str = ""
    NMAP_OPTS: str = "-sV --script=vuln"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
