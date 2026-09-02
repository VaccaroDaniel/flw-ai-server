from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    scoring_mode: str = Field(default="mock", alias="FLW_SCORING_MODE")
    ollama_base_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    request_timeout_seconds: int = Field(default=120, alias="REQUEST_TIMEOUT_SECONDS")
    whisper_backend: str = Field(default="faster_whisper", alias="WHISPER_BACKEND")
    whisper_model: str = Field(default="tiny", alias="WHISPER_MODEL")
    whisper_device: str = Field(default="cpu", alias="WHISPER_DEVICE")
    whisper_compute_type: str = Field(default="int8", alias="WHISPER_COMPUTE_TYPE")
    whisper_local_files_only: bool = Field(default=True, alias="WHISPER_LOCAL_FILES_ONLY")
    whisper_command: str = Field(default="", alias="WHISPER_COMMAND")


@lru_cache
def get_settings() -> Settings:
    return Settings()
