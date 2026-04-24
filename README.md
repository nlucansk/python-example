# FastAPI AKS Boilerplate

FastAPI app with Azure Workload Identity for AKS. Connects to Key Vault and Storage Account using `DefaultAzureCredential`.

## Quick Start

### Local Development (with Docker)

```bash
# Build
docker build -t fastapi-app .

# Run without Azure (health checks pass, Azure endpoints return 404)
docker run -p 8000:8000 fastapi-app

# Run with Azure (requires `az login` or service principal env vars)
docker run -p 8000:8000 \
  -e APP_AZURE_KEYVAULT_URL=https://my-vault.vault.azure.net/ \
  -e APP_AZURE_STORAGE_ACCOUNT_URL=https://myaccount.blob.core.windows.net \
  -e AZURE_CLIENT_ID=<sp-client-id> \
  -e AZURE_TENANT_ID=<tenant-id> \
  -e AZURE_CLIENT_SECRET=<sp-secret> \
  fastapi-app
```

Open http://localhost:8000/docs for Swagger UI.

### Local Development (with uv)

```bash
uv sync --all-extras
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest tests/ -v
```

### Run Tests (Docker, no uv needed)

```bash
docker build -t fastapi-app-test --target builder -f - . <<'EOF'
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /build
COPY pyproject.toml ./
RUN uv lock && uv sync --no-install-project
COPY src/ src/
COPY tests/ tests/
RUN uv sync
EOF

docker run --rm fastapi-app-test uv run --extra dev pytest tests/ -v
```

## Endpoints

| Path | Auth | Description |
|------|------|-------------|
| `GET /docs` | - | Swagger UI |
| `GET /healthz` | - | Liveness probe (always 200) |
| `GET /readyz` | - | Readiness probe (checks KV + Storage) |
| `GET /api/items` | - | Example CRUD (in-memory) |
| `GET /api/azure/keyvault/secrets` | - | List Key Vault secret names |
| `GET /api/azure/keyvault/secrets/{name}` | - | Get secret value |
| `GET /api/azure/storage/containers` | - | List blob containers |
| `GET /api/azure/storage/containers/{name}/blobs` | - | List blobs |

## Deploy to AKS

### Prerequisites

1. AKS cluster with **OIDC issuer** and **workload identity** addon enabled
2. Azure Managed Identity with federated credential pointing to K8s ServiceAccount `boilerplate/fastapi-app`
3. RBAC grants on the Managed Identity:
   - `Key Vault Secrets User` on the Key Vault
   - `Storage Blob Data Contributor` on the Storage Account
4. Container image pushed to ACR

### Setup Workload Identity

```bash
# Enable on existing cluster
az aks update -g <rg> -n <cluster> --enable-oidc-issuer --enable-workload-identity

# Get OIDC issuer URL
OIDC_ISSUER=$(az aks show -g <rg> -n <cluster> --query "oidcIssuerProfile.issuerUrl" -o tsv)

# Create managed identity
az identity create -g <rg> -n fastapi-app-identity
CLIENT_ID=$(az identity show -g <rg> -n fastapi-app-identity --query clientId -o tsv)

# Create federated credential (binds K8s SA to managed identity)
az identity federated-credential create \
  -g <rg> \
  --identity-name fastapi-app-identity \
  --name fastapi-app-fedcred \
  --issuer $OIDC_ISSUER \
  --subject system:serviceaccount:boilerplate:fastapi-app \
  --audiences api://AzureADTokenExchange

# Grant RBAC
az role assignment create --assignee $CLIENT_ID --role "Key Vault Secrets User" --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>
az role assignment create --assignee $CLIENT_ID --role "Storage Blob Data Contributor" --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>
```

### Deploy

```bash
# Update k8s/serviceaccount.yaml with your CLIENT_ID
# Update k8s/deployment.yaml with your ACR image and Azure URLs

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify
kubectl -n boilerplate get pods
kubectl -n boilerplate logs -l app=fastapi-app
```

### How Workload Identity Works

No secrets needed. The AKS mutating webhook automatically injects these into your pod:
- `AZURE_CLIENT_ID` — your managed identity
- `AZURE_TENANT_ID` — your AAD tenant
- `AZURE_FEDERATED_TOKEN_FILE` — projected SA token path
- `AZURE_AUTHORITY_HOST` — AAD endpoint

`DefaultAzureCredential` picks these up automatically. Same code works locally (using `az login` or env vars) and in AKS (using workload identity).

## Configuration

All settings use `APP_` prefix (to avoid colliding with Azure-injected vars):

| Env Var | Default | Description |
|---------|---------|-------------|
| `APP_APP_NAME` | `fastapi-aks-boilerplate` | App name in logs |
| `APP_DEBUG` | `false` | Debug mode |
| `APP_LOG_LEVEL` | `INFO` | Log level (DEBUG for console output) |
| `APP_AZURE_KEYVAULT_URL` | `` | Key Vault URL |
| `APP_AZURE_STORAGE_ACCOUNT_URL` | `` | Storage account URL |
| `APP_AZURE_STORAGE_CONTAINER` | `default` | Default container name |
