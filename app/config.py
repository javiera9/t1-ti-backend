from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str

    encryption_key: str
    cookie_secret: str

    as_client_id: str
    as_client_secret: str

    app_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # Servidor de Autenticacion del curso (fijo, no cambia entre estudiantes)
    as_base_url: str = "https://tarea1-auth-z2fqxmm2ja-uc.a.run.app"


settings = Settings()
