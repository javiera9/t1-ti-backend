# Informe Arquitectura - Tarea 1 IIC3103
Javiera Martínez Amadei

21203903 - jimartinez4@uc.cl

## Arquitectura aplicación

Para esta tarea se decidió optar por trabajar con 2 repositorios separados para el backend y frontend, donde el frontend se comunica con el backend mediante un API explicada a continuación.

El repositorio del backend se llama `t1-ti-backend` y el del frontend se llama `t1-ti-frontend`. Por una parte, `t1-ti-backend` se trabajó en Python y FastAPI, donde se envían las solicitudes en formato JSON. Por otra parte, `t1-ti-frontend` se trabajó usando React, Vite y JavaScript simple. La decisión de trabajar con estos lenguajes y frameworks fue simplemente por simplicidad y familiarización con estas tecnologías, ya que habían sido usadas en proyectos y ramos anteriores.

En `t1-ti-frontend` nunca maneja credenciales ni secretos, esa responsabilidad vive exclusivamente en el `t1-ti-backend`, donde se cifran antes de guardarse. Este se encarga de conectar los servicios de base de datos (en este caso, Supabase), hacer la conexión al Authorizaiton Server (AS) y a los MCP's, y hacer el llamado correspondiente a cada tool de los MCP's descritos en el enunciado. Se construyó una API (FastAPI) aquí que permite estas conexiones, la cual se detalla en el archivo `app/main.py`.

Para montar la aplicación, se optó por utilizar Render, en donde `t1-ti-backend` se construyó como un Web Service, mientras que `t1-ti-frontend` como un Static Website. Cada servicio tiene sus respectivas variables de entorno, las cuales se detalla su descripción a continuación:

`t1-ti-backend`:
- SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY: conexión a la base de datos.
- ENCRYPTION_KEY: encargada de cifrar los `client_secret` y tokens antes de guardalos en la base de datos.
- COOKIE_SECRET: firma la cookie de la sesión para que haga el viaje de manera segura (login usuario + `state` y `code_verifier`). `code_verifier` nace del `code_challenge` hasheándolo, es su versión mejorada ya que así nadie puede interferir con el URL y hacer solicitudes en nombre de otro usuario. `code` es generado por el AS luego de que el usuario se logea. 
- AS_CLIENT_ID/AS_CLIENT_SECRET: credenciales del cliente OAuth para el login de la app.
- APP_BASE_URL: URL propia del backend, a partir de ella se arman los `redirect_uri`.
- FRONTEND_URL: URL del frontend, se usa para saber a dónde redirigir luego de logearse y conectar un MCP.

`t1-ti-frontend`:
- VITE_API_BASE_URL: URL del backend para saber de dónde obtener la información.

A continuación, se detalla la función que cumplen los archivos clave de ambos repositorios:

`t1-ti-backend`:

_ai-logs:_
- `ai-logs/sesion-principal.md`: historial de conversación que se tuvo durante toda la realización de la tarea. Se utilizó Claude Code.
- `ai-logs/conversacion-mcps-oauth.md`: historial de conversación que se tuvo al comenzar a hacer la tarea para entender bien cómo funcionaba el flujo OAuth y su conexión con los MCP's, con el fin de entender los contenidos antes de ponerse a hacer código.

_app:_
- `app/config.py`: lee las variables de entorno. 
- `app/db.py`: para conectar a Supabase.
- `app/dcr.py`: para hacer el registro dinámico de clientes según el protocolo DCR para Staywell.
- `app/main.py`: FastAPI del backend, conecta todas las rutas, desde el login hasta las tools.
- `app/mcp_client.py`: llama al protocolo MCP (tools/list y tools/calls) además de manejar el refresh automátio de tokens vencidos.
- `app/mcp_oauth.py`: para cualquier MCP conectado hace el registro dinámico de los clientes según la librería Authlib. 
- `app/oauth.py`: registra al cliente desde el login.
- `app/security.py`: se encarga de cifrar/descifrar las variables que sean secretas, como el JWT entregado por el AS cuando se guarda o las variables como client_secret, a través de AES-256-GCM.

_routes:_
- `routes/auth.py`: rutas de login, logout, redirigir y para saber si como usuario estoy logeado.
- `routes/cimd.py`: expone el documento de metadata autoreferencial (JSON) que este protocolo necesita.
- `routes/mcp.py`: rutas de conexión y desconexión de MCP's, redirección, listado y llamado de tools de cada MCP.

_db:_
- `db/schema.sql`: respaldo del modelo de datos (PostgreSQL) cargado en Supabase.

_scripts:_
- `scripts/export_ai_log.py`: busca replicar la conversación que se tuvo con Claude Code.
- `scripts/seed_mcp_server.py`: busca insertar a mano (siguiendo el protocolo PRE) el cliente registrado cifrando `client_secret`.

`t1-ti-frontend`:
_ai-logs:_

Lo mismo que en backend.

_src:_
- `src/api.js`: trae la API del backend y centraliza sus llamadas.
- `src/App.jsx`: define las rutas (raíz, dashboard, MCP's).
- `src/Dashboard.jsx`: lista los 3 MCP's con su estado (conectado/desconectado) según el usuario que esté logeado.
- `src/DynamicForm.jsx`: genera los formularios dinámicos de cada tool de cada MCP a partir del schema de los argumentos (inputSchema).
- `src/index.css`: estilos de la página.
- `src/Landing.jsx`: página de llegada, botón para iniciar sesión.
- `src/main.jsx`: conecta las páginas con React.
- `src/Tools.jsx`: lista las tools de los MCP's conectados, con su formulario dinámico y schema.

## Modelo ER
![Diagrama ER](<ER TI Diagram.png>)

## Diagrama de secuencia MCP - Conexión PRE (Login)
Secuencia normal de lo que sucede al logearse en la página.

![alt text](<Login PRE.png>)

## Diagrama de secuencia MCP - Conexión PRE (Andes Air)
Prácticamente la misma estructura que el diagrama de Login, pero esta vez confirma que haya una sesión activa para continuar con el proceso.

![alt text](<Andes Air PRE.png>)

## Diagrama de secuencia MCP - Conexión DCR (Staywell)
En este protocolo los clientes no se generan a mano, sino que entre servidores se maneja la creación del cliente a través del POST para registro.

![alt text](<Staywell DCR.png>)

## Diagrama de secuencia MCP - Conexión CMID (Cielo Sur)
En este protocolo el client_id cambia a la URL fija (backend) y no se envía el client_secret (no tiene).

![alt text](<Cielo Sur CMID.png>)