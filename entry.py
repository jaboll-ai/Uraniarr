import backend.main as main
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

main.app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@main.app.get("/{full_path:path}") 
async def spa_fallback(full_path: str): return FileResponse("frontend/dist/index.html")


if __name__ == "__main__":
    import uvicorn
    access_log=os.getenv("ACCESS_LOG", "false").lower() in ("true", "t", "1", "yes", "on")
    log_level=os.getenv("LOG_LEVEL", "info").lower()
    log_level=log_level if log_level in ('critical', 'error', 'warning', 'info', 'debug', 'trace') else "info"
    uvicorn.run(main.app, host="0.0.0.0", port=8000, access_log=access_log, log_level=log_level)