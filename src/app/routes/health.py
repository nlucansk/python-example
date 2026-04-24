from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", status_code=status.HTTP_200_OK)
async def liveness():
    """Liveness probe: app process is running."""
    return {"status": "alive"}


@router.get("/readyz", status_code=status.HTTP_200_OK)
async def readiness(request: Request):
    """Readiness probe: downstream dependencies are reachable."""
    azure = request.app.state.azure
    checks = {
        "keyvault": await azure.check_keyvault(),
        "storage": await azure.check_storage(),
    }
    all_ok = all(checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ready" if all_ok else "not_ready", "checks": checks},
    )
