# scripts/obtener_refresh_token.py
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# Cambia el scope si necesitas acceso completo a Drive
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def main():
    # Ruta a tu credentials.json descargado de Google Cloud Console
    creds_path = Path("secrets/credentials.json").resolve()
    if not creds_path.exists():
        raise FileNotFoundError(f"No se encontró {creds_path}")

    # Flujo de app de escritorio: abrirá el navegador y pedirá consentimiento
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(host="localhost", port=0, prompt="consent")

    # Mostrar y guardar tokens
    print("\nCLIENT_ID:", creds.client_id)
    print("CLIENT_SECRET:", creds.client_secret)
    print("ACCESS_TOKEN:", creds.token)
    print("REFRESH_TOKEN:", creds.refresh_token)

    # Opcional: guardar en token.json (no subir al repo)
    token_path = Path("secrets/token.json")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with token_path.open("w", encoding="utf-8") as f:
        json.dump({
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "scopes": SCOPES
        }, f, indent=2)
    print(f"\nTokens guardados en {token_path}")

if __name__ == "__main__":
    main()