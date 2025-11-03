import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Cargar credenciales desde st.secrets (Cloud) o .env (local)
client_id = st.secrets["DRIVE_CLIENT_ID"]
client_secret = st.secrets["DRIVE_CLIENT_SECRET"]
refresh_token = st.secrets["DRIVE_REFRESH_TOKEN"]
scope = st.secrets.get("DRIVE_SCOPE", "https://www.googleapis.com/auth/drive.file")

# Construir credenciales
creds = Credentials(
    None,
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret,
    scopes=[scope],
)

# Crear servicio de Drive
service = build("drive", "v3", credentials=creds)

# Probar listando los 5 primeros archivos de la carpeta
folder_id = st.secrets["DRIVE_FOLDER_ID"]
results = service.files().list(
    q=f"'{folder_id}' in parents",
    pageSize=5,
    fields="files(id, name, createdTime, size)"
).execute()

files = results.get("files", [])

st.subheader("🔎 Test de conexión con Google Drive")
if not files:
    st.info("No se encontraron archivos en la carpeta de Drive.")
else:
    for f in files:
        st.write(f"📂 {f['name']} ({f['id']}) - {f.get('size','?')} bytes")