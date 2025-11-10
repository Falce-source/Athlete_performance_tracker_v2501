"""
Módulo de gestión de backups en Google Drive.
Encapsula toda la lógica de autenticación y operaciones CRUD sobre backups.
"""

from datetime import datetime
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io


# --- Inicialización de credenciales ---
def _get_service():
    creds = Credentials(
        None,
        refresh_token=os.getenv("DRIVE_REFRESH_TOKEN"),
        client_id=os.getenv("DRIVE_CLIENT_ID"),
        client_secret=os.getenv("DRIVE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=[os.getenv("DRIVE_SCOPE", "https://www.googleapis.com/auth/drive.file")]
    )
    return build("drive", "v3", credentials=creds)


# --- Funciones públicas ---

def subir_backup(local_path: str, remote_name: str = None) -> str:
    """
    Sube un archivo local a la carpeta de backups en Drive.
    Devuelve el file_id del archivo creado.
    """
    service = _get_service()
    folder_id = os.getenv("DRIVE_FOLDER_ID")

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
    folder_id = os.getenv("DRIVE_FOLDER_ID")

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