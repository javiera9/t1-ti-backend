-- IntegraTrip — esquema de base de datos (Supabase/Postgres)
-- Tarea 1, IIC3103 Taller de Integracion, 2026-2.
--
-- Respaldo versionado del schema aplicado en el proyecto de Supabase (via su SQL editor).
-- Es la misma definicion que vive documentada en CLAUDE.md; mantener ambos sincronizados
-- si se modifica el modelo de datos.

create table public.users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.mcp_servers (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  protocol_type text not null check (protocol_type in ('PRE','DCR','CMID')),
  server_url text not null,        -- = "resource" en authorize/token, y endpoint MCP real (incluye /mcp)
  metadata_url text not null,      -- discovery: /realms/{realm}/.well-known/openid-configuration
  client_id text,
  client_secret_enc bytea,         -- NULL en Cielo Sur (CMID no usa secret)
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.mcp_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  mcp_server_id uuid not null references public.mcp_servers(id) on delete cascade,
  access_token_enc bytea not null,
  refresh_token_enc bytea,
  token_expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, mcp_server_id)
);

alter table public.users enable row level security;
alter table public.mcp_servers enable row level security;
alter table public.mcp_connections enable row level security;

-- RLS esta activado sin politicas a proposito: el backend usa la service_role key
-- y la salta de todas formas; esto solo protege contra un uso accidental de la anon key.
-- No hay tabla de oauth_transactions: el state/code_verifier vive solo en la cookie
-- firmada de SessionMiddleware durante el flujo OAuth (ver CLAUDE.md).
