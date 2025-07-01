from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from backend.db import engine
from backend.routers import tapi, mapi, api, nzbapi
from backend.exceptions import BaseError

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO ENV
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SQLModel.metadata.create_all(engine)

@app.exception_handler(BaseError)
async def handle_scrape_error(request: Request, exc: BaseError):
    return JSONResponse(status_code=exc.status_code or 404, content={"detail": exc.detail or "", "type": exc.type}) 


app.include_router(tapi.router)
app.include_router(mapi.router)
app.include_router(nzbapi.router)
app.include_router(api.router)
