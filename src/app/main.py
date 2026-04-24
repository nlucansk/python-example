from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.azure_clients import AzureClients
from app.config import Settings
from app.logging import setup_logging
from app.middleware import RequestLoggingMiddleware
from app.routes import azure as azure_routes
from app.routes import health, items

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init Azure clients. Shutdown: close them."""
    settings = Settings()
    setup_logging(settings.log_level)

    azure = AzureClients(settings)
    await azure.connect()
    app.state.azure = azure
    app.state.settings = settings

    await logger.ainfo("startup", app=settings.app_name)
    yield
    await logger.ainfo("shutdown", app=settings.app_name)

    await azure.close()


app = FastAPI(
    title="FastAPI AKS Boilerplate",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.include_router(health.router)
app.include_router(items.router)
app.include_router(azure_routes.router)
