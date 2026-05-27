import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes import router
from server.database import init_db

# Configure enterprise logging (Fix Q20)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern startup and shutdown sequence (Fix Q4)."""
    logger.info("Starting up server, initializing database schema...")
    init_db()
    yield
    logger.info("Shutting down server...")

app = FastAPI(title="Secure Messenger", lifespan=lifespan)

# CORS Configuration - Allows web client interactions from any origin (Bonus 2)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)