from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file("secrets/credentials.json", SCOPES)

    # Generar URL de autorización
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    print("Abre esta URL en tu navegador:", auth_url)

    # Copia el 'code' que Google te devuelve en la redirección
    code = input("Pega aquí el 'code' de la URL de redirección: ")

    # Intercambiar el code por tokens
    flow.fetch_token(code=code)

    creds = flow.credentials
    print("\nACCESS_TOKEN:", creds.token)
    print("REFRESH_TOKEN:", creds.refresh_token)

if __name__ == "__main__":
    main()