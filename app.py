import streamlit as st
from src.interfaz import perfil
from src.interfaz import calendario   # ← nuevo
from dotenv import load_dotenv
import os

# Cargar variables desde .env
load_dotenv()

DRIVE_CLIENT_ID = os.getenv("DRIVE_CLIENT_ID")
DRIVE_CLIENT_SECRET = os.getenv("DRIVE_CLIENT_SECRET")
DRIVE_REFRESH_TOKEN = os.getenv("DRIVE_REFRESH_TOKEN")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
DRIVE_SCOPE = os.getenv("DRIVE_SCOPE", "https://www.googleapis.com/auth/drive.file")

st.subheader("🔐 Verificación de secrets")

try:
    st.write("Client ID cargado:", bool(st.secrets["DRIVE_CLIENT_ID"]))
    st.write("Client Secret cargado:", bool(st.secrets["DRIVE_CLIENT_SECRET"]))
    st.write("Refresh Token cargado:", bool(st.secrets["DRIVE_REFRESH_TOKEN"]))
    st.write("Folder ID cargado:", bool(st.secrets["DRIVE_FOLDER_ID"]))
    st.write("Scope:", st.secrets.get("DRIVE_SCOPE"))
    st.success("✅ Todos los secrets están accesibles")
except Exception as e:
    st.error(f"Error al leer secrets: {e}")

# Validación temprana
missing = [k for k, v in {
    "DRIVE_CLIENT_ID": DRIVE_CLIENT_ID,
    "DRIVE_CLIENT_SECRET": DRIVE_CLIENT_SECRET,
    "DRIVE_REFRESH_TOKEN": DRIVE_REFRESH_TOKEN,
    "DRIVE_FOLDER_ID": DRIVE_FOLDER_ID
}.items() if not v]
if missing:
    raise RuntimeError(f"Faltan variables de entorno: {', '.join(missing)}")

# ─────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Athlete Performance Tracker v2501",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# NAVEGACIÓN LATERAL
# ─────────────────────────────────────────────
st.sidebar.title("🏋️ Athlete Performance Tracker")
opcion = st.sidebar.radio(
    "Navegación",
    [
        "🏠 Inicio",
        "👤 Perfil atleta",
        "📅 Calendario",   # ← nuevo
        # "📊 Métricas",
        # "🧪 Tests",
        # "🏋️ Fuerza",
        # "🍽️ Nutrición",
        # "💬 Comentarios",
        # "⚙️ Configuración"
    ]
)

# ─────────────────────────────────────────────
# CONTENIDO PRINCIPAL
# ─────────────────────────────────────────────
if opcion == "🏠 Inicio":
    st.title("Athlete Performance Tracker v2501")
    st.write("Bienvenido. Selecciona una sección en el menú lateral.")

elif opcion == "👤 Perfil atleta":
    perfil.mostrar_perfil()

elif opcion == "📅 Calendario":
    calendario.mostrar_calendario()