from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="Test Case Generator",
    description="Functional & Negative Test Case Generator",
    version="1.0.0"
)

# ---------------------------------------------------------
# 🛡 CORS CONFIG — WAJIB untuk React/Vite
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # nanti kalau production bisa ganti whitelist domain
    allow_credentials=True,
    allow_methods=["*"],            # penting supaya OPTIONS tidak error!
    allow_headers=["*"],
)

# ---------------------------------------------------------
# API ROUTER
# ---------------------------------------------------------
app.include_router(api_router)
