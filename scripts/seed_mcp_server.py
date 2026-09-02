"""Inserta o actualiza una fila en mcp_servers, cifrando el client_secret
antes de guardarlo. Se corre a mano, una vez por MCP (o de nuevo si cambian
las credenciales), y nunca requiere pegar el secreto en el chat con Claude.

Uso:
    python3 scripts/seed_mcp_server.py \
        --name andes_air \
        --protocol PRE \
        --server-url https://tarea1-mcp-pre-z2fqxmm2ja-uc.a.run.app/mcp \
        --metadata-url https://tarea1-auth-z2fqxmm2ja-uc.a.run.app/realms/pre/.well-known/openid-configuration \
        --client-id pre_XXXXXXXX

Te va a pedir el client_secret de forma interactiva (no queda en el historial
de la shell). Para CMID (Cielo Sur, sin client_secret) usa --no-secret.
"""

import argparse
import getpass
import sys

sys.path.insert(0, ".")

from app.db import supabase  # noqa: E402
from app.security import encrypt_for_db  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="andes_air | staywell | cielo_sur")
    parser.add_argument("--protocol", required=True, choices=["PRE", "DCR", "CMID"])
    parser.add_argument("--server-url", required=True)
    parser.add_argument("--metadata-url", required=True)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--no-secret", action="store_true", help="usar para CMID")
    args = parser.parse_args()

    row = {
        "name": args.name,
        "protocol_type": args.protocol,
        "server_url": args.server_url,
        "metadata_url": args.metadata_url,
        "client_id": args.client_id,
    }

    if not args.no_secret:
        secret = getpass.getpass(f"client_secret para '{args.name}': ")
        row["client_secret_enc"] = encrypt_for_db(secret)

    result = supabase.table("mcp_servers").upsert(row, on_conflict="name").execute()
    print(f"OK: guardado '{args.name}' (id={result.data[0]['id']})")


if __name__ == "__main__":
    main()
