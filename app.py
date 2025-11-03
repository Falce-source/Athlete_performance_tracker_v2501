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

if st.button("📤 Crear backup de base.db"):
    try:
        if not os.path.exists("base.db"):
            st.error("No se encontró base.db en el directorio principal")
        else:
            file_id = backup_storage.subir_backup("base.db")
            st.success(f"Backup de base.db subido correctamente con ID: {file_id}")
    except Exception as e:
        st.error(f"Error al subir backup: {e}")

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
            # Antes de sobrescribir base.db, hacemos copia de seguridad local
            if os.path.exists("base.db"):
                os.rename("base.db", "base.db.bak")
            destino = "base.db"
            try:
                backup_storage.descargar_backup(file_id, destino)
                st.success(f"Backup restaurado y sobrescrito en {destino} (copia previa en base.db.bak)")
            except Exception as e:
                if os.path.exists("base.db.bak"):
                    os.rename("base.db.bak", "base.db")
                st.error(f"Error en restauración, se recuperó la copia local: {e}")
    else:
        st.info("No hay backups disponibles para restaurar.")
except Exception as e:
    st.error(f"Error al cargar lista de backups: {e}")

# ─────────────────────────────────────────────
# VALIDACIÓN AUTOMÁTICA DEL FLUJO CRUD DE BACKUPS
# ─────────────────────────────────────────────
st.subheader("✅ Validación completa de backups")

if st.button("🚀 Ejecutar validación CRUD"):
    try:
        report = []

        # 1. Subida
        file_id = backup_storage.subir_backup("base.db")
        report.append(f"📤 Subida OK → ID: {file_id}")

        # 2. Listado
        backups = backup_storage.listar_backups()
        if backups:
            report.append(f"📋 Listado OK → {len(backups)} backups encontrados")
        else:
            report.append("❌ Listado vacío")

        # 3. Rotación
        backup_storage.rotar_backups(max_backups=5)
        report.append("♻️ Rotación OK (máx. 5 backups)")

        # 4. Restauración
        if backups:
            file_id = backups[0]["id"]
            if os.path.exists("base.db"):
                os.rename("base.db", "base.db.bak")
            backup_storage.descargar_backup(file_id, "base.db")
            report.append(f"📥 Restauración OK → {backups[0]['name']} descargado")

        # Mostrar informe
        st.success("Validación completada")
        for line in report:
            st.write(line)

    except Exception as e:
        st.error(f"Error en validación CRUD: {e}")

# ─────────────────────────────────────────────
# DASHBOARD VISUAL DE BACKUPS
# ─────────────────────────────────────────────
st.subheader("📊 Dashboard de Backups en Drive")

try:
    backups = backup_storage.listar_backups(max_results=20)
    if backups:
        import pandas as pd

        # Convertimos a DataFrame para mostrar tabla con tamaños legibles
        def format_size(size):
            if not size:
                return "-"
            size = int(size)
            for unit in ["B","KB","MB","GB"]:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024

        df = pd.DataFrame(backups)
        df = df.rename(columns={
            "name": "Nombre",
            "createdTime": "Fecha creación",
            "size": "Tamaño",
            "id": "ID"
        })
        df["Tamaño"] = df["Tamaño"].apply(format_size)
        st.dataframe(df[["Nombre", "Fecha creación", "Tamaño"]])

        # Selección de backup
        opciones = {f"{b['name']} ({b['createdTime']})": b['id'] for b in backups}
        seleccion = st.selectbox("Selecciona un backup para acción:", list(opciones.keys()))
        file_id = opciones[seleccion]

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Restaurar seleccionado", key="restore_btn"):
                if os.path.exists("base.db"):
                    os.rename("base.db", "base.db.bak")
                backup_storage.descargar_backup(file_id, "base.db")
                st.success(f"Backup restaurado en base.db (copia previa en base.db.bak)")

        with col2:
            confirmar = st.checkbox("Confirmar eliminación", key="confirm_delete")
            if st.button("🗑️ Eliminar seleccionado", key="delete_btn") and confirmar:
                service = backup_storage._get_service()
                service.files().delete(fileId=file_id).execute()
                st.warning(f"Backup eliminado: {seleccion}")
            elif st.button("🗑️ Eliminar seleccionado", key="delete_btn_disabled") and not confirmar:
                st.info("Marca la casilla de confirmación antes de eliminar.")
    else:
        st.info("No hay backups en la carpeta.")
except Exception as e:
    st.error(f"Error al cargar dashboard de backups: {e}")

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