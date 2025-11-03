import streamlit as st
from src.interfaz import perfil
from src.interfaz import calendario   # ← nuevo
from dotenv import load_dotenv
import os
import backup_storage

# Cargar variables desde .env
load_dotenv()

DRIVE_CLIENT_ID = os.getenv("DRIVE_CLIENT_ID")
DRIVE_CLIENT_SECRET = os.getenv("DRIVE_CLIENT_SECRET")
DRIVE_REFRESH_TOKEN = os.getenv("DRIVE_REFRESH_TOKEN")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
DRIVE_SCOPE = os.getenv("DRIVE_SCOPE", "https://www.googleapis.com/auth/drive.file")

st.subheader("💾 Gestión de Backups")

if st.button("📤 Subir backup de prueba"):
    try:
        # Creamos un archivo temporal de prueba
        test_file = "test_backup.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Backup de prueba OK")

        file_id = backup_storage.subir_backup(test_file)
        st.success(f"Archivo subido correctamente con ID: {file_id}")
    except Exception as e:
        st.error(f"Error al subir archivo: {e}")

if st.button("📋 Listar backups"):
    try:
        backups = backup_storage.listar_backups()
        if not backups:
            st.info("No hay backups en la carpeta.")
        for b in backups:
            st.write(f"{b['name']} ({b['createdTime']}) - {b.get('size','?')} bytes")
    except Exception as e:
        st.error(f"Error al listar backups: {e}")

if st.button("♻️ Rotar backups"):
    try:
        backup_storage.rotar_backups(max_backups=5)
        st.success("Rotación completada")
    except Exception as e:
        st.error(f"Error al rotar backups: {e}")

# ─────────────────────────────────────────────
# DESCARGA Y RESTAURACIÓN DE BACKUPS
# ─────────────────────────────────────────────
st.subheader("📥 Restaurar backup")

try:
    backups = backup_storage.listar_backups()
    if backups:
        opciones = {f"{b['name']} ({b['createdTime']})": b['id'] for b in backups}
        seleccion = st.selectbox("Selecciona un backup para restaurar:", list(opciones.keys()))

        if st.button("📥 Descargar y restaurar"):
            file_id = opciones[seleccion]
            destino = "restaurado.db"  # aquí defines la ruta de restauración
            backup_storage.descargar_backup(file_id, destino)
            st.success(f"Backup restaurado en {destino}")
    else:
        st.info("No hay backups disponibles para restaurar.")
except Exception as e:
    st.error(f"Error al cargar lista de backups: {e}")

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