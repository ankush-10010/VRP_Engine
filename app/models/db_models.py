from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db.base import Base

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True, index=True) # UUID
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Store results (could be large, so we use JSON type)
    result = Column(JSON, nullable=True)

class GeocodedLocation(Base):
    """
    Cache for geocoded addresses to save API costs/time.
    """
    __tablename__ = "geocoded_locations"

    original_address = Column(String, primary_key=True, index=True)
    formatted_address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
