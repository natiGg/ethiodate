from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    redis_url: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
    
    @property
    def get_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if "sslmode=" in url:
            url = url.replace("sslmode=", "ssl=")
        if "channel_binding=" in url:
            # asyncpg doesn't support channel_binding query param
            import re
            url = re.sub(r'&?channel_binding=[^&]*', '', url)
        return url

settings = Settings()
