from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file(
    "secrets/token.json", SCOPES
)
creds = flow.run_local_server(port=0)

print("Refresh token:", creds.refresh_token)
print("Access token:", creds.token)
