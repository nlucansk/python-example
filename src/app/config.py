from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # App
    app_name: str = "fastapi-aks-boilerplate"
    debug: bool = False
    log_level: str = "INFO"

    # Azure Key Vault (e.g. https://my-vault.vault.azure.net/)
    azure_keyvault_url: str = ""

    # Azure Blob Storage (e.g. https://myaccount.blob.core.windows.net)
    azure_storage_account_url: str = ""
    azure_storage_container: str = "default"
