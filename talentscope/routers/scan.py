import asyncio
from fastapi import APIRouter, BackgroundTasks
from services.ingestion import run_scan

router = APIRouter()

_scan_running = False


@router.post("/scan/run")
async def trigger_scan(background_tasks: BackgroundTasks):
    """Kick off a scan in the background and return immediately."""
    global _scan_running
    if _scan_running:
        return {"status": "already_running", "jobs_new": 0}

    async def _run():
        global _scan_running
        _scan_running = True
        try:
            await run_scan()
        finally:
            _scan_running = False

    background_tasks.add_task(_run)
    return {"status": "started", "jobs_new": 0}


@router.get("/scan/status")
async def scan_status():
    return {"running": _scan_running}
