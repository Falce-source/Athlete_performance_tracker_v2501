from google_auth_oauthlib.flow import Flow
import json
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive"]

def main():
    creds_path = Path("secrets/credentials.json").resolve()
    flow = Flow.from_client_secrets_file(
        str(creds_path),
        scopes=SCOPES,
        redirect_uri="https://athleteperformancetrackerv2501.streamlit.app"
    )

    # Generar URL de autorización
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    print("\nAbre esta URL en tu navegador y acepta permisos:\n", auth_url)

    # Copia el parámetro 'code' de la URL de redirección y pégalo aquí
    code = input("\nPega aquí el parámetro 'code' de la URL: ")
    flow.fetch_token(code=code)

    creds = flow.credentials
    print("\nACCESS_TOKEN:", creds.token)
    print("REFRESH_TOKEN:", creds.refresh_token)

    # Guardar tokens en secrets/token.json
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