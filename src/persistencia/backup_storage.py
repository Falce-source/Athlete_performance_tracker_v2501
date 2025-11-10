"""
Módulo de gestión de backups en Google Drive.
Encapsula autenticación y operaciones CRUD sobre backups.
Versión OAuth (con refresh tokens desde st.secrets["google_drive"]).
"""

from datetime import datetime
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import os
import json
import requests
import time

def _load_oauth_cfg():
    """Carga configuración OAuth desde st.secrets['google_drive']."""
    gd = st.secrets.get("google_drive", {})
    required = ["client_id", "client_secret", "token_uri", "scope"]
    missing = [k for k in required if not gd.get(k)]
    if missing:
        st.error(f"❌ Falta en secrets[google_drive]: {', '.join(missing)}")
        return None
    return {
        "client_id": gd["client_id"],
        "client_secret": gd["client_secret"],
        "token_uri": gd["token_uri"],
        "scope": gd.get("scope", "https://www.googleapis.com/auth/drive.file"),
        "refresh_token": gd.get("refresh_token", ""),
        "access_token": gd.get("access_token", ""),
        "expires_at": gd.get("expires_at", 0),
        "folder_id": gd.get("folder_id", ""),  # opcional
    }
def _refresh_access_token(cfg: dict) -> str:
    """Refresca el access_token usando refresh_token; actualiza st.secrets en runtime."""
    if not cfg.get("refresh_token"):
       st.error("❌ Falta refresh_token en secrets[google_drive]. Ejecuta el login inicial.")
       return ""
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "refresh_token": cfg["refresh_token"],
        "grant_type": "refresh_token",
    }
    r = requests.post(cfg["token_uri"], data=data, timeout=30)
    try:
        r.raise_for_status()
    except Exception as e:
        st.error(f"❌ Error al refrescar access_token: {e}")
        return ""
    payload = r.json()
    access_token = payload.get("access_token", "")
    expires_in = payload.get("expires_in", 3600)
    if not access_token:
        st.error("❌ Respuesta sin access_token al refrescar.")
        return ""
    # Actualiza en memoria (st.secrets es de solo lectura persistente; aquí solo reflejamos runtime)
    cfg["access_token"] = access_token
    cfg["expires_at"] = int(time.time()) + int(expires_in) - 30  # margen
    return access_token

def _ensure_access_token(cfg: dict) -> str:
    """Devuelve un access_token válido; refresca si está vacío o caducado."""
    now = int(time.time())
    token = cfg.get("access_token", "")
    expires_at = int(cfg.get("expires_at", 0))
    if not token or now >= expires_at:
        return _refresh_access_token(cfg)
    return token

def _get_service():
    """Inicializa cliente Drive usando OAuth tokens desde secrets."""
    cfg = _load_oauth_cfg()
    if not cfg:
        return None
    token = _ensure_access_token(cfg)
    if not token:
        return None
    try:
        return build("drive", "v3", developerKey=None, credentials=None, requestBuilder=None, cache_discovery=False,
                    )  # usamos http headers manualmente en cada llamada
    except Exception as e:
        # Fallback al cliente estándar con discovery (crearemos recurso vía googleapiclient build con cred adaptada)
        pass
    # Construcción con credenciales via google-auth-transport-requests (manual)
    try:
        from google.auth.credentials import Credentials as BaseCreds
        class BearerCreds(BaseCreds):
            def __init__(self, token):
                super().__init__()
                self.token = token
            def refresh(self, request):  # no hacer nada; gestionamos refresh fuera
                return
            @property
            def expired(self):
                return False
            @property
            def valid(self):
                return True if self.token else False
        creds = BearerCreds(token)
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        st.error(f"❌ Error al inicializar cliente Drive (OAuth): {e}")
        return None

# --- Funciones públicas ---

def subir_backup(local_path: str, remote_name: str = None) -> str:
    """
    Sube un archivo local a la carpeta de backups en Drive.
    Devuelve el file_id del archivo creado.
    """
    service = _get_service()
    if service is None:
        return ""

    cfg = _load_oauth_cfg()
    folder_id = cfg.get("folder_id", "")
    if remote_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.basename(local_path)
        name, ext = os.path.splitext(base)
        remote_name = f"{name}_{timestamp}{ext}"

    file_metadata = {"name": remote_name, "parents": [folder_id]}
    media = MediaFileUpload(local_path, resumable=True)

    # Ejecuta con header Authorization Bearer
    access_token = _ensure_access_token(cfg)
    if not access_token:
        return ""
    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name"
        ).execute(http=service._http)  # http ya usa creds Bearer
    except Exception:
        # En algunos entornos, googleapiclient toma creds del objeto service; si falla, reconstruimos con creds Bearer
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
    if service is None:
        return []

    cfg = _load_oauth_cfg()
    folder_id = cfg.get("folder_id", "")
    query = f"'{folder_id}' in parents and trashed=false"

    access_token = _ensure_access_token(cfg)
    if not access_token:
        return []
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
    if service is None:
        return

    backups = listar_backups(max_results=100)  # obtenemos todos
    if len(backups) > max_backups:
        for old in backups[max_backups:]:
            service.files().delete(fileId=old["id"]).execute()


def descargar_backup(file_id: str, destino: str) -> None:
    """
    Descarga un backup desde Drive y lo guarda en destino local.
    """
    service = _get_service()
    if service is None:
        return

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(destino, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()