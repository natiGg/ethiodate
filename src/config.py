from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    redis_url: str
    admin_ids: str = "" # Comma separated list of admin telegram IDs

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    
    @property
    def get_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")
        if "channel_binding=" in url:
            import re
            url = re.sub(r'&?channel_binding=[^&]*', '', url)
        return url
        
    @property
    def get_admin_ids(self) -> list[int]:
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip().isdigit()]

settings = Settings()
