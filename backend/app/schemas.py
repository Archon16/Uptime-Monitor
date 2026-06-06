from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UrlBase(BaseModel):
    url: str
    name: Optional[str] = None


class UrlCreate(UrlBase):
    pass


class UrlResponse(UrlBase):
    id: int
    is_up: Optional[bool] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    last_checked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
