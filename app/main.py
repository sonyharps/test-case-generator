from fastapi import FastAPI
from app.api.router import api_router
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="Test Case Generator",
    description="Functional & Negative Test Case Generator",
    version="1.0.0"
)

app.include_router(api_router)
