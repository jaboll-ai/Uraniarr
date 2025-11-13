import asyncio
from contextlib import suppress
from typing import Optional
from backend.dependencies import get_error_logger, get_logger
from backend.services.filehelper import scan_and_move_all_files, rescan_files, reimport_files

mapping = {
    "import_files": {
        "interval_attr": "import_poll_interval",
        "task_coro": scan_and_move_all_files,
        "name": "ImportJob",
    },
    "check_deleted": {
        "interval_attr": "rescan_interval",
        "task_coro": rescan_files,
        "name": "CheckFileAvailabilityJob",
    },
    "reimport": {
        "interval_attr": "reimport_interval",
        "task_coro": reimport_files,
        "name": "ImportForeignJob",
    },
}

def get_tasks(state):
    if getattr(state, "tasks", None) is None:
        state.tasks = {}
    return state.tasks

def get_job_by_interval(key: str):
    for k, v in mapping.items():
        if v["interval_attr"] == key:
            return k


def get_job_args(key: str):
    if key not in mapping:
        raise ValueError(f"Unknown task key: {key}")
    return mapping[key]

def init_jobs(state):
    for key in ("import_files", "check_deleted", "reimport"):
        if not key in get_tasks(state):
            get_tasks(state)[key] = asyncio.create_task(periodic_task(state, **get_job_args(key)))

def start_job(state, key: str):
    tasks = get_tasks(state)
    if key in tasks and not tasks[key].done():
        get_logger().debug(f"Start called on {get_job_args(key)['name']}")
        return
    get_tasks(state)[key] = asyncio.create_task(periodic_task(state, **get_job_args(key)))

async def stop_job(state, key: str):
    task = get_tasks(state).get(key)
    if task:
        with suppress(Exception):
            task.cancel()
        with suppress(asyncio.CancelledError):
            await task

async def restart_job(state, key: str):
    await stop_job(state, key)
    get_tasks(state)[key] = asyncio.create_task(periodic_task(state, **get_job_args(key)))

async def stop_jobs(state):
    await asyncio.gather(*[stop_job(state, key) for key in get_tasks(state)])

async def restart_jobs(state):
    await stop_jobs(state)
    init_jobs(state)

async def periodic_task(state, interval_attr: str, task_coro, name: Optional[str]):
    while True:
        if getattr(state.cfg_manager, interval_attr) <= 0:
            get_logger().info((f"Disabling {name or task_coro.__name__}"))
            break
        try:
            get_logger().debug(f"Running {name or task_coro.__name__} ...")
            await task_coro(state)
        except BaseException as e:
            get_error_logger().exception(e)
            get_logger().error(f"{name or task_coro.__name__} failed: {e}")
        await asyncio.sleep(getattr(state.cfg_manager, interval_attr))