# ai-logs

Historial de conversaciones con el agente de IA (Claude Code) usado para desarrollar esta tarea, versionado para cumplir la seccion "Uso de IA" del enunciado.

Como el trabajo se hizo en paralelo en `t1-ti-backend` y `t1-ti-frontend`, cada sesion que toco ambos repos se guarda identica en los dos, para no depender de cual termine siendo "el" repositorio final.

`sesion-principal.md` es el chat de trabajo principal (continuo a lo largo de toda la tarea) — no se genera un archivo nuevo cada dia, se **regenera y sobreescribe** el mismo archivo al cerrar cada dia de trabajo, apuntando siempre al mismo `.jsonl` (que va creciendo). El historial de commits sobre ese archivo muestra el avance incremental dia a dia. Si en algun momento se abre un chat genuinamente distinto (otra sesion, otro tema), ese si se guarda como archivo aparte con su propia fecha.

## Como (re)generar el log (al cerrar por el dia)

1. Encuentra el archivo `.jsonl` de la sesion en:
   ```
   ~/.claude/projects/<carpeta-de-trabajo-codificada>/<session-id>.jsonl
   ```
   (la carpeta codificada reemplaza cada `/` del path por `-`; el de la sesion principal es el mismo desde el primer dia — se puede identificar por ser el mas grande / el que tiene la fecha de modificacion mas reciente)
2. Corre:
   ```bash
   python3 scripts/export_ai_log.py <ruta-al-archivo.jsonl> ai-logs/sesion-principal.md
   ```
3. Revisa el `.md` generado (no deberia tener secretos ni tokens; el script ya omite el contenido de las imagenes/adjuntos y el detalle interno de las tool calls, solo deja un resumen).
4. Commitea el `.md` junto con el resto de los cambios de esa sesion (asi el commit de cada dia deja registro del avance).
