# IntegraTrip — Backend

Cliente MCP para IIC3103 - Taller de Integración (Tarea 1, semestre 2026-2). Conecta a tres servidores MCP externos (Andes Air, StayWell, Cielo Sur), cada uno con un protocolo OAuth 2.0 distinto (PRE, DCR, CMID).

**Deadline: viernes 4 de septiembre, 18:00.** El código de este repo debe reflejar fielmente lo desplegado y quedar disponible 2 semanas para corrección.

## Instrucciones para Claude Code

Antes de escribir cualquier código relacionado con OAuth o con un servidor MCP, revisa la sección "Servidor de Autenticación (AS)" de este archivo — ahí está todo lo necesario. Si necesitas un detalle que no está cubierto acá, la documentación completa del AS vive en `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/docs` (usa WebFetch si hace falta profundizar en algo puntual, pero lo esencial ya está resuelto abajo, no hace falta releerla completa).

## Stack

- **Backend**: Python, FastAPI — API pura (JSON), sin servir HTML. El frontend vive aparte en `t1-ti-frontend` (React + Vite, JavaScript plano — no TypeScript, la autora no tiene experiencia previa con TS) y consume esta API. Decisión 2026-09-01: se probó consolidar todo en un servicio Python con Jinja2, pero se revirtió — la autora prefiere trabajar con React, que ya conoce, antes que aprender Jinja2 bajo presión de tiempo.
- **Base de datos**: Supabase (PostgreSQL), plan gratuito, accedido vía `supabase-py` con la service role key (bypassa RLS a propósito).
- **OAuth**: Authlib (`authlib.integrations.starlette_client`) + `SessionMiddleware` de Starlette (maneja `state`/PKCE con una cookie firmada durante el tránsito del flujo OAuth — no se persiste en base de datos)
- **CORS**: habilitado solo para el origen del frontend (`FRONTEND_URL`), con `allow_credentials=True` porque la sesión de login viaja en cookie.
- **Despliegue**: Render (Web Service para este backend; el frontend se despliega aparte)

## Regla de arquitectura no negociable

El frontend **nunca** habla directo con Supabase, con el Authorization Server (AS), ni con ningún servidor MCP. Todo pasa por la API de este backend. El frontend no debe recibir ni manejar tokens, secrets, ni credenciales de ningún tipo.

## Variables de entorno (backend-only — nunca en el frontend, nunca en git)

| Variable | Propósito |
|---|---|
| `SUPABASE_SERVICE_ROLE_KEY` | Conexión a Supabase con permisos totales, saltando RLS |
| `ENCRYPTION_KEY` | Cifra/descifra (AES-256-GCM) cualquier columna `_enc` antes de guardarla o justo después de leerla |
| `COOKIE_SECRET` | Firma la cookie de `SessionMiddleware` que guarda `state`/`code_verifier` durante el tránsito OAuth |
| `AS_CLIENT_ID` / `AS_CLIENT_SECRET` | Cliente OAuth (realm `pre`) usado **solo** para el login de esta app — no pertenece a ningún MCP, por eso vive en env var y no en la tabla `mcp_servers` |

Las credenciales de Andes Air, StayWell y Cielo Sur (`client_id`/`client_secret_enc`) **no** van en variables de entorno — viven en la tabla `mcp_servers`, tratadas las tres igual.

## Esquema de base de datos (Supabase/Postgres) — versión final

También vive como respaldo versionado en [`db/schema.sql`](db/schema.sql) — si se modifica el modelo, actualizar ambos.

```sql
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
```

No hay tabla de `oauth_transactions`: el `state`/`code_verifier` vive solo en la cookie firmada de `SessionMiddleware` durante el flujo; `user_id` viaja en la sesión de login del usuario (ya autenticado antes de conectar un MCP) y `mcp_server_id` en la ruta de la URL (ej. `/connect/andes_air`).

RLS está activado sin políticas a propósito: el backend usa `service_role` y lo salta igual; esto solo protege contra un uso accidental de la `anon key`.

## Servidor de Autenticación (AS) del curso — referencia

Base: `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app`
JWKS compartido (los 3 realms): `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/.well-known/jwks.json` (kid `iic3103-tarea1`, RS256)
Docs completas: `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/docs`

### Los tres realms

| Realm | Servicio | ¿client_secret? | server_url (MCP) | metadata_url (discovery) |
|---|---|---|---|---|
| `pre` | Andes Air | Sí | `https://tarea1-mcp-pre-z2fqxmm2ja-uc.a.run.app/mcp` | `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/realms/pre/.well-known/openid-configuration` |
| `dcr` | StayWell | Sí | `https://tarea1-mcp-dcr-z2fqxmm2ja-uc.a.run.app/mcp` | `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/realms/dcr/.well-known/openid-configuration` |
| `cimd` | Cielo Sur | No | `https://tarea1-mcp-cimd-z2fqxmm2ja-uc.a.run.app/mcp` | `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/realms/cimd/.well-known/openid-configuration` |

Registro DCR: `POST https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/realms/dcr/register` (RFC 7591, JSON). Se hace **una sola vez** (la primera vez que cualquier usuario conecta StayWell), el `client_id`/`client_secret` resultante se guarda en la fila de `mcp_servers`, y se reutiliza para todos los usuarios después. Opcionalmente se puede mandar `Authorization: Bearer <access_token_de_login>` para asociar el cliente registrado a la cuenta y que aparezca en `/console`.

Registro CMID: el `client_id` es la URL HTTPS pública de un JSON que expone este mismo backend (aún no construido — ver Pendientes). Ese JSON debe traer su propia URL como valor de `client_id` adentro (autorreferencial). No usa `client_secret`.

Registro PRE: se hace a mano en `https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/console`, una vez, y el `client_id`/`client_secret` resultante se guarda en la fila de Andes Air en `mcp_servers`.

### Reglas del flujo OAuth (aplican a los 3 realms)

- **PKCE (S256) y el parámetro `resource` son obligatorios** — no opcionales. Con Authlib usando `server_metadata_url` (la `metadata_url` de la tabla de arriba), PKCE se activa solo porque la metadata declara `code_challenge_methods_supported: ["S256"]`.
- `resource` = la URL exacta del MCP (`server_url` de la tabla), y queda grabada como claim `aud` en el JWT resultante. Un JWT con `aud` de un MCP no sirve para otro MCP, ni para el login.
- `scope` es siempre `"mcp:tools"` en los tres realms — es una constante, no varía por servidor.
- `redirect_uri` debe coincidir exactamente (carácter a carácter) con uno registrado para ese cliente. Registrar tanto la URL de localhost (desarrollo) como la de Render (producción).
- El `code` del callback vive 5 minutos y es de un solo uso.
- `access_token`: TTL 3600s (1 hora). `refresh_token`: dura 30 días, y **rota** en cada uso (el anterior queda inválido de inmediato — guardar siempre el más reciente).
- No hay `id_token` separado — un solo `access_token` (JWT) trae todo: `iss`, `sub` (= email UC), `aud`, `scope`, `client_id`, `email`, `student_id`, `iat`, `exp`.

### Login de la app (no es una conexión a MCP)

Usa el **mismo realm `pre`** que Andes Air, pero con `client_id`/`client_secret` **distintos** (los de `AS_CLIENT_ID`/`AS_CLIENT_SECRET`, no los de Andes Air) y `resource` = el origen de esta app (no la URL de un MCP). Para forzar que otro usuario pueda loguearse después de un logout (sin arrastrar sesión previa del AS), agregar `&prompt=login` a la URL de `/authorize`.

## Tools disponibles por MCP (para pruebas de humo, en este orden de prioridad)

- **Andes Air**: `list_airports`, `search_flights`, `get_flight`, `book_flight`, `list_bookings`, `cancel_booking`, `whoami` (probar primero — no requiere parámetros y confirma que el Bearer token funciona)
- **StayWell**: `search_hotels`, `get_hotel`, `book_hotel`, `list_bookings`, `cancel_booking`
- **Cielo Sur**: `list_cities`, `get_current_weather`, `get_forecast`, `get_weather_alerts`

## Requisitos funcionales (resumen del enunciado)

1. Landing page + login/logout; tras logout, otro usuario debe poder loguearse sin ver conexiones del anterior
2. Ver MCPs conectados del usuario actual; conectar uno nuevo según su protocolo; persistido y scoped por usuario
3. `tools/list` por MCP conectado, mostrado de forma clara
4. `tools/call` con formulario dinámico generado desde `inputSchema` de cada tool
5. Resultados de `tools/call` mostrados con padding/scroll adecuado, sin romper el layout ni desbordar horizontalmente, aunque sea JSON extenso

## Prioridades según la rúbrica del curso

DCR (20%) + CIMD (20%) + Listar tools (20%) = 60% de la nota — bastante más que PRE (10%) o Login (10%). Priorizar tiempo ahí; PRE sirve principalmente para validar que el flujo base funciona antes de replicarlo en los otros dos.

## Seguridad (no negociable, penalización directa si se incumple)

- Nunca exponer secretos/tokens/API keys en el frontend, ni en JS del navegador, ni en localStorage/sessionStorage
- Nunca subir credenciales al repositorio Git (`.env` en `.gitignore` desde el día uno)
- `client_secret_enc`, `access_token_enc`, `refresh_token_enc` siempre cifrados en la base, nunca en texto plano

## Pendientes / decisiones abiertas

- [ ] Crear en `/console` los dos clientes PRE (uno para login, otro para Andes Air) y guardar sus credenciales
- [ ] Construir el endpoint propio de metadata JSON para CMID (debe estar desplegado antes de poder probar ese flujo)
- [ ] Definir el contrato de la API entre este backend y el frontend (endpoints, formato de request/response)

## Despliegue

Render, plan gratuito. Servicio tipo "Web Service" para este backend. Variables de entorno configuradas en el dashboard de Render, no en el código.
