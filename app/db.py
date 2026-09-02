from supabase import create_client, Client

from app.config import settings

# Cliente con service_role: salta RLS a proposito (RLS esta activo solo como
# resguardo contra el uso accidental de la anon key, que este backend no usa).
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
