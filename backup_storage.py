"""
Módulo de gestión de backups en Google Drive.
Encapsula toda la lógica de autenticación y operaciones CRUD sobre backups.
"""

from datetime import datetime
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import os

def _oauth_flow():
    """Lanza flujo OAuth y devuelve servicio Drive si el admin autoriza."""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["gdrive"]["client_id"],
                "client_secret": st.secrets["gdrive"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=[st.secrets["gdrive"].get("scope", "https://www.googleapis.com/auth/drive.file")],
    )
    flow.redirect_uri = st.secrets["gdrive"]["redirect_uri"]

    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    st.markdown(f"[Haz clic aquí para autorizar Google Drive]({auth_url})")

    code = st.experimental_get_query_params().get("code")
    if code:
        flow.fetch_token(code=code[0])
        st.session_state.credentials = flow.credentials
        st.success("✅ Nuevo refresh token generado")
        st.write("Nuevo refresh_token:", flow.credentials.refresh_token)
        st.info("⚠️ Copia este refresh_token en st.secrets[gdrive] para que quede persistente tras reinicios.")
        return build("drive", "v3", credentials=flow.credentials)

    return None

def _get_service():
    rt = st.secrets["gdrive"].get("refresh_token")
    if not rt:
        st.warning("⚠️ No hay refresh_token en secrets, inicia autorización.")
        return _oauth_flow()

    try:
        creds = Credentials(
            None,
            refresh_token=rt,
            client_id=st.secrets["gdrive"]["client_id"],
            client_secret=st.secrets["gdrive"]["client_secret"],
            token_uri="https://oauth2.googleapis.com/token",
            scopes=[st.secrets["gdrive"].get("scope", "https://www.googleapis.com/auth/drive.file")]
        )
        creds.refresh(Request())
        return build("drive", "v3", credentials=creds)
    except RefreshError as e:
        st.warning(f"⚠️ Refresh token inválido: {e}")
        return _oauth_flow()

# --- Funciones públicas ---

def subir_backup(local_path: str, remote_name: str = None) -> str:
    """
    Sube un archivo local a la carpeta de backups en Drive.
    Devuelve el file_id del archivo creado.
    """
    service = _get_service()
    folder_id = st.secrets["gdrive"]["folder_id"]

    if remote_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.basename(local_path)
        name, ext = os.path.splitext(base)
        remote_name = f"{name}_{timestamp}{ext}"

    file_metadata = {"name": remote_name, "parents": [folder_id]}
    media = MediaFileUpload(local_path, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name"
    ).execute()

    return file.get("id")

def listar_backups(max_results: int = 10) -> list[dict]:
    """
    Lista los últimos backups en la carpeta de Drive.
    Devuelve una lista de diccionarios con id, nombre y fecha.
    """
    service = _get_service()
    folder_id = st.secrets["gdrive"]["folder_id"]

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        pageSize=max_results,
        orderBy="createdTime desc",
        fields="files(id, name, createdTime, size)"
    ).execute()

    return results.get("files", [])


def rotar_backups(max_backups: int = 5) -> None:
    """
    Mantiene solo los últimos N backups en la carpeta de Drive.
    Elimina los más antiguos.
    """
    service = _get_service()
    backups = listar_backups(max_results=100)  # obtenemos todos

    if len(backups) > max_backups:
        for old in backups[max_backups:]:
            service.files().delete(fileId=old["id"]).execute()


def descargar_backup(file_id: str, destino: str) -> None:
    """
    Descarga un backup desde Drive y lo guarda en destino local.
    """
    service = _get_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(destino, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()