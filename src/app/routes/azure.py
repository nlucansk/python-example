from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/azure", tags=["azure"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class SecretName(BaseModel):
    name: str
    id: str


class SecretValue(BaseModel):
    name: str
    value: str | None


class ContainerInfo(BaseModel):
    name: str


class BlobInfo(BaseModel):
    name: str
    size: int | None = None
    content_type: str | None = None


class ErrorDetail(BaseModel):
    detail: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_keyvault(request: Request):
    client = request.app.state.azure.keyvault
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key Vault client is not configured",
        )
    return client


def _get_blob(request: Request):
    client = request.app.state.azure.blob
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage Account client is not configured",
        )
    return client


# ---------------------------------------------------------------------------
# Key Vault endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/keyvault/secrets",
    response_model=list[SecretName],
    responses={404: {"model": ErrorDetail}, 500: {"model": ErrorDetail}},
)
async def list_secrets(request: Request) -> list[SecretName]:
    """List secret names from Azure Key Vault (names/IDs only, not values)."""
    kv = _get_keyvault(request)
    try:
        secrets: list[SecretName] = []
        async for prop in kv.list_properties_of_secrets():
            secrets.append(SecretName(name=prop.name, id=prop.id or ""))
        return secrets
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Key Vault secrets: {exc}",
        ) from exc


@router.get(
    "/keyvault/secrets/{secret_name}",
    response_model=SecretValue,
    responses={404: {"model": ErrorDetail}, 500: {"model": ErrorDetail}},
)
async def get_secret(request: Request, secret_name: str) -> SecretValue:
    """Retrieve a specific secret value from Azure Key Vault."""
    kv = _get_keyvault(request)
    try:
        secret = await kv.get_secret(secret_name)
        return SecretValue(name=secret.name, value=secret.value)
    except Exception as exc:
        error_msg = str(exc)
        if "SecretNotFound" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret '{secret_name}' not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve secret '{secret_name}': {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Storage Account endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/storage/containers",
    response_model=list[ContainerInfo],
    responses={404: {"model": ErrorDetail}, 500: {"model": ErrorDetail}},
)
async def list_containers(request: Request) -> list[ContainerInfo]:
    """List blob containers in the configured Azure Storage Account."""
    blob_svc = _get_blob(request)
    try:
        containers: list[ContainerInfo] = []
        async for container in blob_svc.list_containers():
            containers.append(ContainerInfo(name=container.name))
        return containers
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list containers: {exc}",
        ) from exc


@router.get(
    "/storage/containers/{container_name}/blobs",
    response_model=list[BlobInfo],
    responses={404: {"model": ErrorDetail}, 500: {"model": ErrorDetail}},
)
async def list_blobs(request: Request, container_name: str) -> list[BlobInfo]:
    """List blobs in a specific container."""
    blob_svc = _get_blob(request)
    try:
        container_client = blob_svc.get_container_client(container_name)
        blobs: list[BlobInfo] = []
        async for blob in container_client.list_blobs():
            blobs.append(
                BlobInfo(
                    name=blob.name,
                    size=blob.size,
                    content_type=blob.content_settings.content_type
                    if blob.content_settings
                    else None,
                )
            )
        return blobs
    except Exception as exc:
        error_msg = str(exc)
        if "ContainerNotFound" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Container '{container_name}' not found",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list blobs in '{container_name}': {exc}",
        ) from exc
