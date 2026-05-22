from fastapi import APIRouter, BackgroundTasks

from ..services.fetcher import fetch_and_store_player_data

router = APIRouter(tags=["fetch"])


@router.post("/api/fetch_now")
async def trigger_fetch_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_and_store_player_data)
    return {"message": "已在后台触发抓取任务"}
