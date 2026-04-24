from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
from azure.storage.blob.aio import BlobServiceClient

from app.config import Settings


class AzureClients:
    """Holds Azure SDK async clients. Created once at startup, closed at shutdown."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.credential: DefaultAzureCredential | None = None
        self.keyvault: SecretClient | None = None
        self.blob: BlobServiceClient | None = None

    async def connect(self) -> None:
        self.credential = DefaultAzureCredential()

        if self._settings.azure_keyvault_url:
            self.keyvault = SecretClient(
                vault_url=self._settings.azure_keyvault_url,
                credential=self.credential,
            )

        if self._settings.azure_storage_account_url:
            self.blob = BlobServiceClient(
                account_url=self._settings.azure_storage_account_url,
                credential=self.credential,
            )

    async def close(self) -> None:
        if self.keyvault:
            await self.keyvault.close()
        if self.blob:
            await self.blob.close()
        if self.credential:
            await self.credential.close()

    async def check_keyvault(self) -> bool:
        """Readiness probe: can we reach Key Vault?"""
        if not self.keyvault:
            return True  # not configured, skip check
        try:
            async for _ in self.keyvault.list_properties_of_secrets():
                break
            return True
        except Exception:
            return False

    async def check_storage(self) -> bool:
        """Readiness probe: can we reach Blob Storage?"""
        if not self.blob:
            return True  # not configured, skip check
        try:
            await self.blob.get_account_information()
            return True
        except Exception:
            return False
