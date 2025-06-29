from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, documents, health

app = FastAPI(
    title="DocProc",
    description="AI-powered document processing and Q&A system",
    version="1.0.0"
)

# Configure CORS origins based on environment
cors_origins = [
    "http://localhost:3000",  # Docker frontend (dev)
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

# Add production origins
if settings.ENVIRONMENT == "production":
    cors_origins.extend([
        "http://localhost:8080",  # Local production test
        "https://localhost:8080", # Local production test with SSL
        # Add your actual production domains here when deploying to AWS
        # "https://yourdomain.com",
        # "https://www.yourdomain.com"
    ])

# add in CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
