import backend.main as main
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

main.app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@main.app.get("/{full_path:path}") 
async def spa_fallback(full_path: str): return FileResponse("frontend/dist/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(main.app, host="0.0.0.0", port=8000)