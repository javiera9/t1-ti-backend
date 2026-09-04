"""Convierte el log crudo (.jsonl) de una sesion de Claude Code en un
transcript legible en Markdown, listo para versionar en el repo (ver
seccion "Uso de IA" del enunciado de la Tarea 1).

Uso:
    python3 export_ai_log.py <ruta-al-archivo.jsonl> <ruta-salida.md>

El .jsonl de la sesion actual vive en:
    ~/.claude/projects/<carpeta-de-trabajo-codificada>/<session-id>.jsonl

(la carpeta codificada reemplaza cada "/" del path por "-"; por ejemplo
~/Desktop/Taller de Integracion pasa a ser
~/.claude/projects/-Users-tu-usuario-Desktop-Taller-de-Integraci-n/)
"""

import json
import re
import sys
from datetime import datetime

TOOL_SUMMARY_KEYS = {
    "Write": "file_path",
    "Edit": "file_path",
    "Read": "file_path",
    "Bash": "command",
    "Glob": "pattern",
    "Grep": "pattern",
}

# Cualquier token largo tipo base64url/hex (asi se ven las API keys, JWTs,
# client_secrets, etc.) se redacta de los comandos que se resumen -- un
# ENCRYPTION_KEY real se colo una vez por un comando de verificacion (grep
# comparando su valor), asi que ahora se filtra automaticamente en vez de
# confiar en que nunca vuelva a pasar.
SECRET_LIKE = re.compile(r"\b[A-Za-z0-9_-]{20,}\b")


def redact(text):
    return SECRET_LIKE.sub("[valor-posiblemente-sensible-redactado]", text)


def summarize_tool_use(block):
    name = block.get("name", "tool")
    inp = block.get("input", {}) or {}
    key = TOOL_SUMMARY_KEYS.get(name)
    if key and key in inp:
        val = redact(str(inp[key]))
        if len(val) > 100:
            val = val[:100] + "..."
        return f"`{name}`: {val}"
    if name == "AskUserQuestion":
        qs = inp.get("questions", [])
        headers = ", ".join(q.get("header", "") for q in qs)
        return f"`AskUserQuestion`: {headers}"
    return f"`{name}`"


def fmt_ts(ts):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts or ""


def main():
    if len(sys.argv) != 3:
        print(f"Uso: python3 {sys.argv[0]} <ruta-al-archivo.jsonl> <ruta-salida.md>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        lines = [json.loads(l) for l in f]

    turns = []  # list of dicts: {speaker, text, tools, ts}
    current_assistant_text = []
    current_assistant_tools = []
    current_ts = None

    def flush_assistant():
        nonlocal current_assistant_text, current_assistant_tools, current_ts
        if current_assistant_text or current_assistant_tools:
            turns.append({
                "speaker": "claude",
                "text": "\n\n".join(current_assistant_text).strip(),
                "tools": current_assistant_tools[:],
                "ts": current_ts,
            })
        current_assistant_text = []
        current_assistant_tools = []
        current_ts = None

    for obj in lines:
        t = obj.get("type")
        msg = obj.get("message", {})
        ts = obj.get("timestamp")

        if t == "user":
            content = msg.get("content")
            has_image = False
            text_parts = []
            is_tool_result_only = False

            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                block_types = [b.get("type") for b in content if isinstance(b, dict)]
                if block_types and all(bt == "tool_result" for bt in block_types):
                    is_tool_result_only = True
                else:
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "text":
                            text_parts.append(b.get("text", ""))
                        elif b.get("type") == "image":
                            has_image = True

            if is_tool_result_only:
                continue

            joined = "\n".join(p for p in text_parts if p).strip()
            if not joined and not has_image:
                continue

            # strip system-reminder blocks for readability
            import re
            joined_clean = re.sub(r"<system-reminder>.*?</system-reminder>", "", joined, flags=re.DOTALL).strip()
            if not joined_clean and has_image:
                joined_clean = "[usuario adjunto una imagen/captura de pantalla]"
            elif has_image:
                joined_clean += "\n\n[+ imagen/captura de pantalla adjunta]"

            if not joined_clean:
                continue

            flush_assistant()
            turns.append({"speaker": "user", "text": joined_clean, "tools": [], "ts": ts})

        elif t == "assistant":
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            if current_ts is None:
                current_ts = ts
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    txt = b.get("text", "").strip()
                    if txt:
                        current_assistant_text.append(txt)
                elif b.get("type") == "tool_use":
                    current_assistant_tools.append(summarize_tool_use(b))

    flush_assistant()

    out = []
    out.append("# Historial de conversacion con agente de IA (Claude Code)\n")
    out.append("Sesion de trabajo en la Tarea 1 de IIC3103 - Taller de Integracion (IntegraTrip). ")
    out.append("Extraido automaticamente del log de sesion de Claude Code para dar cumplimiento al requisito de ")
    out.append("versionar las conversaciones sostenidas con el agente (seccion \"Uso de IA\" del enunciado).\n")

    for turn in turns:
        speaker = "Usuario" if turn["speaker"] == "user" else "Claude"
        ts_str = fmt_ts(turn["ts"]) if turn["ts"] else ""
        header = f"## {speaker}" + (f" — {ts_str}" if ts_str else "")
        out.append(header)
        if turn["text"]:
            out.append(turn["text"])
        if turn["tools"]:
            out.append("\n**Acciones ejecutadas:**")
            for tool_line in turn["tools"]:
                out.append(f"- {tool_line}")
        out.append("")

    result = "\n\n".join(out)
    with open(sys.argv[2], "w") as f:
        f.write(result)
    print(f"Escrito {len(result)} caracteres, {len(turns)} turnos, en {sys.argv[2]}")


if __name__ == "__main__":
    main()
