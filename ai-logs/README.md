# ai-logs

Historial de conversaciones con el agente de IA (Claude Code) usado para desarrollar esta tarea, versionado para cumplir la seccion "Uso de IA" del enunciado.

Como el trabajo se hizo en paralelo en `t1-ti-backend` y `t1-ti-frontend`, cada sesion que toco ambos repos se guarda identica en los dos, para no depender de cual termine siendo "el" repositorio final.

## Como generar un nuevo log (al cerrar una sesion de trabajo)

1. Encuentra el archivo `.jsonl` de la sesion en:
   ```
   ~/.claude/projects/<carpeta-de-trabajo-codificada>/<session-id>.jsonl
   ```
   (la carpeta codificada reemplaza cada `/` del path por `-`; el mas reciente es el que tiene la fecha de modificacion mas nueva)
2. Corre:
   ```bash
   python3 scripts/export_ai_log.py <ruta-al-archivo.jsonl> ai-logs/AAAA-MM-DD-nombre-corto.md
   ```
3. Revisa el `.md` generado (no deberia tener secretos ni tokens; el script ya omite el contenido de las imagenes/adjuntos y el detalle interno de las tool calls, solo deja un resumen).
4. Commitea el `.md` junto con el resto de los cambios de esa sesion.
