from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import create_doc, validate_doc
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

cors_origins_raw = os.getenv("CORS_ORIGINS", "")
origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
if not origins:
    origins = ["http://localhost", "localhost",  "http://127.0.0.1", "http://192.168.100.215:8080", "http://192.168.100.215", "http://localhost:8080", "https://taskflow-frontend-pqok.onrender.com", "https://taskflow-frontend-pqok.onrender.com/boards", "https://taskflow-frontend-pqok.onrender.com/dashboard", "https://taskflow-frontend-pqok.onrender.com/cronograma"]

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(
    create_doc.router,
    prefix="/api/v1",
    tags=["Create_doc"]
)

app.include_router(
    validate_doc.router,
    prefix="/api/v1",
    tags=["Validate_doc"]
)

@app.get("/api/v1/health")
def status():
    return {"server_status":"ok"}
