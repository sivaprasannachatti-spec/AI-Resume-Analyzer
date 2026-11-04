from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.database import create_db_and_tables
from backend.routes.resume_routes import router as resume_router
from backend.routes.cv_routes import router as cv_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    create_db_and_tables()
    yield


from fastapi.responses import JSONResponse
from fastapi.requests import Request

app = FastAPI(
    title="AI Resume Analyzer & ATS Optimization Engine",
    description="Full-stack AI Career Platform powered by Docling, OpenRouter, and deterministic ATS scoring.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend (local dev & production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensures even uncaught server exceptions return a valid JSON payload with CORS headers."""
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )

from backend.routes.auth_routes import router as auth_router

# Register API Routers
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(cv_router)


@app.get("/")
async def root():
    return {
        "platform": "AI Resume Analyzer & ATS Optimization Engine",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "resume": "/api/resume",
            "cv": "/api/cv"
        }
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
