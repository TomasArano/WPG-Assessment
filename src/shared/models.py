from pydantic import BaseModel, Field
from datetime import datetime

class SeismicEvent(BaseModel):
    """
    Represents a seismic event signature.
    Enforces strict physical and geographical boundaries.
    """
    eid: int = Field(..., description="Event ID, natural number")
    timestamp: datetime = Field(..., description="Event UTC timestamp")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Hypocenter latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Hypocenter longitude")
    depth: float = Field(..., ge=-100.0, le=0.0, description="Hypocenter depth")
    Mw: float = Field(..., ge=0.0, le=9.0, description="Earthquake magnitude")
    dist: float = Field(..., gt=0.0, description="Distance from location")
    azi: float = Field(..., ge=-180.0, le=180.0, description="Azimuth")
    loclat: float = Field(..., ge=-90.0, le=90.0, description="Location latitude")
    loclon: float = Field(..., ge=-180.0, le=180.0, description="Location longitude")