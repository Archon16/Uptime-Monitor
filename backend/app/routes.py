from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models import Url
from app.schemas import UrlCreate, UrlResponse, HealthResponse

router = APIRouter()


@router.post("/urls", response_model=UrlResponse, status_code=201)
async def create_url(url_data: UrlCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Url).where(Url.url == url_data.url))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="URL already exists")

    new_url = Url(url=url_data.url, name=url_data.name)
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)
    return new_url


@router.get("/urls", response_model=list[UrlResponse])
async def list_urls(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Url).order_by(Url.created_at.desc()))
    urls = result.scalars().all()
    return urls


@router.delete("/urls/{url_id}", status_code=204)
async def delete_url(url_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(delete(Url).where(Url.id == url_id))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="URL not found")
    return None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}
