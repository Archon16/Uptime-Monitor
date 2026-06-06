import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.database import AsyncSessionLocal
from app.models import Url


scheduler = None


async def check_url(url_row: Url) -> dict:
    start = datetime.utcnow()
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url_row.url)
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "id": url_row.id,
            "is_up": response.status_code < 400,
            "status_code": response.status_code,
            "response_time_ms": elapsed,
        }
    except Exception:
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        return {
            "id": url_row.id,
            "is_up": False,
            "status_code": None,
            "response_time_ms": elapsed,
        }


async def check_all_urls():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Url))
        urls = result.scalars().all()

        if not urls:
            return

        tasks = [check_url(u) for u in urls]
        results = await asyncio.gather(*tasks)

        for res in results:
            url_obj = await session.get(Url, res["id"])
            if url_obj:
                url_obj.is_up = res["is_up"]
                url_obj.status_code = res["status_code"]
                url_obj.response_time_ms = res["response_time_ms"]
                url_obj.last_checked_at = datetime.utcnow()
                session.add(url_obj)

        await session.commit()


def start_scheduler():
    global scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_all_urls, IntervalTrigger(seconds=60))
    scheduler.start()


def stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown()
