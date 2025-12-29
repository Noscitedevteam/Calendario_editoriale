from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth, brands, projects, posts, generation

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Noscite Calendar API",
    description="API per generazione calendari editoriali con AI",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(brands.router, prefix="/api/brands", tags=["Brands"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])
app.include_router(generation.router, prefix="/api/generate", tags=["AI Generation"])

@app.get("/")
def root():
    return {"message": "Noscite Calendar API", "status": "running"}

@app.get("/api/health")
def api_health():
    return {"status": "healthy", "service": "noscite-calendar"}
