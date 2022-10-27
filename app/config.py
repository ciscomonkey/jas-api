from pydantic import BaseSettings


class Settings(BaseSettings):
    base_dir: str = None
    base_url: str = None
    openapi_url: str = "/openapi.json"
    root_path: str = None
    token: str

    class Config:
        env_file = ".env"
