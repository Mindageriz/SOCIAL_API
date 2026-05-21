from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine, Base
import models  # ensure models are registered before create_all
from routers import auth, posts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create all tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Posts API", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(posts.router)


@app.get("/")
async def root():
    return {"message": "Posts API is running"}
