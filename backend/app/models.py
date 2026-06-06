from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Url(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, nullable=False)
    name = Column(String(255))
    is_up = Column(Boolean, default=False)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    last_checked_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
