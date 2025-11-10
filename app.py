import sys, os
sys.path.append(os.path.dirname(__file__))
import streamlit as st
st.set_page_config(
    page_title="Athlete Performance Tracker v2501",
    layout="wide",
    initial_sidebar_state="expanded"
)
import src.interfaz.perfil as perfil
import src.interfaz.calendario as calendario
import src.interfaz.usuarios as usuarios
import src.interfaz.auditoria as auditoria
import src.interfaz.historial_validaciones as historial_validaciones
from dotenv import load_dotenv
import os
import src.persistencia.backup_storage as backup_storage
from src.interfaz import auth
import src.persistencia.sql as sql

sql.ensure_schema()  # Parche temporal para columnas propietario_id y atleta_usuario_id

# --- RECUPERACIÓN ADMIN INICIAL ---
from src.utils.seguridad import hash_password
if not sql.obtener_usuario_por_email("admin@demo.com"):
    ph = hash_password("admin123")
    sql.crear_usuario(
        nombre="Administrador",
        email="admin@demo.com",
        rol="admin",
        password_hash=ph
    )
    print("✅ Admin inicial recreado")

# Si no hay sesión, mostrar login y detener el resto
if "USUARIO_ID" not in st.session_state or "ROL_ACTUAL" not in st.session_state:
    logged = auth.login_form()
    st.stop()

rol_actual = st.session_state["ROL_ACTUAL"]
usuario_id = st.session_state["USUARIO_ID"]
usuario_nombre = st.session_state.get("USUARIO_NOMBRE", "—")

# Barra lateral con identidad fija
st.sidebar.markdown(f"**🧑 Usuario activo:** {usuario_nombre} (Rol: {rol_actual})")
if st.sidebar.button("Cerrar sesión"):
    auth.logout()

# Importar control de roles
from src.utils.roles import tabs_visibles_por_rol

# Cargar variables desde .env (local) o st.secrets (Cloud)
load_dotenv()

def get_secret(section, key, default=None):
    # Prioriza st.secrets en Cloud, si no existe usa os.getenv (local)
    if section in st.secrets and key in st.secrets[section]:
        return st.secrets[section][key]
    return os.getenv(key, default)

CLIENT_ID = st.secrets["gdrive"]["client_id"]
CLIENT_SECRET = st.secrets["gdrive"]["client_secret"]
REFRESH_TOKEN = st.secrets["gdrive"]["refresh_token"]
FOLDER_ID = st.secrets["gdrive"]["folder_id"]
SCOPE = st.secrets["gdrive"].get("scope", "https://www.googleapis.com/auth/drive.file")

# ─────────────────────────────────────────────
# NAVEGACIÓN LATERAL
# ─────────────────────────────────────────────
st.sidebar.title("🏋️ Athlete Performance Tracker")

# Rol actual y usuario_id obtenidos de sesión/login real
rol_actual = st.session_state.get("ROL_ACTUAL", "admin")
usuario_id = st.session_state.get("USUARIO_ID", 0)

# Mostrar usuario activo en la barra lateral
if rol_actual in ["entrenadora", "atleta"]:
    usuarios = sql.obtener_usuarios()
    nombre_usuario = next((u.nombre for u in usuarios if u.id_usuario == usuario_id), "—")
    st.sidebar.markdown(f"**🧑 Usuario activo:** {nombre_usuario} (ID {usuario_id})")
elif rol_actual == "admin":
    st.sidebar.markdown("**🧑 Usuario activo:** Administrador")

# Pestañas visibles según rol
tabs_visibles = tabs_visibles_por_rol(rol_actual)

# Mapeo de etiquetas a nombres internos
TAB_LABELS = {
    "Inicio": "🏠 Inicio",
    "Perfil Atleta": "👤 Perfil atleta",
    "Calendario": "📅 Calendario",
    "Usuarios": "👥 Usuarios",
    "Backups": "💾 Backups",
    "Auditoria": "🔍 Auditoría",
    "Historial de Validaciones": "📈 Historial de Validaciones",
}

labels_visibles = [TAB_LABELS[t] for t in tabs_visibles if t in TAB_LABELS]

opcion = st.sidebar.radio("Navegación", labels_visibles)

# ─────────────────────────────────────────────
# CONTENIDO PRINCIPAL (según pestaña elegida)
# ─────────────────────────────────────────────
if opcion == "🏠 Inicio":
    st.title("Athlete Performance Tracker v2501")
    st.write("Bienvenido. Selecciona una sección en el menú lateral.")

elif opcion == "👤 Perfil atleta":
    perfil.mostrar_perfil(rol_actual=rol_actual, usuario_id=usuario_id)

elif opcion == "📅 Calendario":
    calendario.mostrar_calendario(rol_actual=rol_actual, usuario_id=usuario_id)

elif opcion == "👥 Usuarios":
    st.title("👥 Gestión de Usuarios")
    # Validación explícita de credenciales Drive
    service = backup_storage._get_service()
    if service is None:
        st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
        st.stop()
    # 🔑 Pasamos rol_actual y usuario_id reales para condicionar permisos
    usuarios.mostrar_usuarios(rol_actual=rol_actual, usuario_id=usuario_id)

elif opcion == "💾 Backups":
    st.title("Gestión de Backups")

    # Bloque explícito de estado de credenciales
    st.subheader("🔑 Estado de credenciales Google Drive")
    service = backup_storage._get_service()
    if service is None:
        st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
        st.stop()
    else:
        st.success("✅ Cliente Drive activo. Puedes listar y subir backups.")

        # Crear / Listar / Rotar
        st.subheader("📤 Crear / Listar / Rotar")
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

        # Restauración manual
        st.subheader("📥 Restaurar backup")
        try:
            backups = backup_storage.listar_backups()
            if backups:
                opciones = {f"{b['name']} ({b['createdTime']})": b['id'] for b in backups}
                seleccion = st.selectbox("Selecciona un backup para restaurar:", list(opciones.keys()))
                if st.button("📥 Descargar y restaurar"):
                    file_id = opciones[seleccion]
                    if os.path.exists("base.db"):
                        if os.path.exists("base.db.bak"):
                            os.remove("base.db.bak")
                        os.rename("base.db", "base.db.bak")
                    destino = "base.db"
                    try:
                        backup_storage.descargar_backup(file_id, destino)
                        st.success(f"Backup restaurado en {destino} (copia previa en base.db.bak)")
                    except Exception as e:
                        if os.path.exists("base.db.bak"):
                            os.rename("base.db.bak", "base.db")
                        st.error(f"Error en restauración, se recuperó la copia local: {e}")
            else:
                st.info("No hay backups disponibles para restaurar.")
        except Exception as e:
            st.error(f"Error al cargar lista de backups: {e}")

        # Validación CRUD
        st.subheader("✅ Validación completa de backups")
        if st.button("🚀 Ejecutar validación CRUD"):
            try:
                report = []
                if not os.path.exists("base.db"):
                    st.error("No se encontró base.db en el directorio principal")
                    st.stop()
                file_id = backup_storage.subir_backup("base.db")
                report.append(f"📤 Subida OK → ID: {file_id}")
                backups = backup_storage.listar_backups()
                if backups:
                    report.append(f"📋 Listado OK → {len(backups)} backups encontrados")
                else:
                    report.append("❌ Listado vacío")
                backup_storage.rotar_backups(max_backups=5)
                report.append("♻️ Rotación OK (máx. 5 backups)")
                if backups:
                    file_id = backups[0]["id"]
                    if os.path.exists("base.db"):
                        if os.path.exists("base.db.bak"):
                            os.remove("base.db.bak")
                        os.rename("base.db", "base.db.bak")
                    backup_storage.descargar_backup(file_id, "base.db")
                    report.append(f"📥 Restauración OK → {backups[0]['name']} descargado")
                st.success("Validación completada")
                for line in report:
                    st.write(line)
            except Exception as e:
                st.error(f"Error en validación CRUD: {e}")

        # Dashboard visual
        st.subheader("📊 Dashboard de Backups en Drive")
        try:
            backups = backup_storage.listar_backups(max_results=20)
            if backups:
                import pandas as pd
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
                opciones = {f"{b['name']} ({b['createdTime']})": b['id'] for b in backups}
                seleccion = st.selectbox("Selecciona un backup para acción:", list(opciones.keys()))
                file_id = opciones[seleccion]
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Restaurar seleccionado", key="restore_btn"):
                        try:
                            if os.path.exists("base.db"):
                                if os.path.exists("base.db.bak"):
                                    os.remove("base.db.bak")
                                os.rename("base.db", "base.db.bak")
                            backup_storage.descargar_backup(file_id, "base.db")
                            st.success("Backup restaurado en base.db (copia previa en base.db.bak)")
                        except Exception as e:
                            if os.path.exists("base.db.bak"):
                                os.rename("base.db.bak", "base.db")
                            st.error(f"Error en restauración, se recuperó la copia local: {e}")
                with col2:
                    confirmar = st.checkbox("Confirmar eliminación", key="confirm_delete")
                    if st.button("🗑️ Eliminar seleccionado", key="delete_btn"):
                        if confirmar:
                            service.files().delete(fileId=file_id).execute()
                            st.warning(f"Backup eliminado: {seleccion}")
                        else:
                            st.info("Marca la casilla de confirmación antes de eliminar.")
            else:
                st.info("No hay backups en la carpeta.")
        except Exception as e:
            st.error(f"Error al cargar dashboard de backups: {e}")
elif opcion == "🔍 Auditoría":
    st.title("🔍 Auditoría")
    service = backup_storage._get_service()
    if service is None:
        st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
        st.stop()
    auditoria.mostrar_auditoria()

elif opcion == "📈 Historial de Validaciones":
    st.title("📈 Historial de Validaciones")
    service = backup_storage._get_service()
    if service is None:
        st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
        st.stop()
    historial_validaciones.mostrar_historial()

    # Crear / Listar / Rotar
    st.subheader("📤 Crear / Listar / Rotar")
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

    # Restauración manual
    st.subheader("📥 Restaurar backup")
    try:
        service = backup_storage._get_service()
        if service is None:
            st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
            st.stop()
        backups = backup_storage.listar_backups()
        if backups:
            opciones = {f"{b['name']} ({b['createdTime']})": b['id'] for b in backups}
            seleccion = st.selectbox("Selecciona un backup para restaurar:", list(opciones.keys()))
            if st.button("📥 Descargar y restaurar"):
                file_id = opciones[seleccion]
                if os.path.exists("base.db"):
                    if os.path.exists("base.db.bak"):
                        os.remove("base.db.bak")
                    os.rename("base.db", "base.db.bak")
                destino = "base.db"
                try:
                    backup_storage.descargar_backup(file_id, destino)
                    st.success(f"Backup restaurado en {destino} (copia previa en base.db.bak)")
                except Exception as e:
                    if os.path.exists("base.db.bak"):
                        os.rename("base.db.bak", "base.db")
                    st.error(f"Error en restauración, se recuperó la copia local: {e}")
        else:
            st.info("No hay backups disponibles para restaurar.")
    except Exception as e:
        st.error(f"Error al cargar lista de backups: {e}")

    # Validación CRUD
    st.subheader("✅ Validación completa de backups")
    if st.button("🚀 Ejecutar validación CRUD"):
        try:
            service = backup_storage._get_service()
            if service is None:
                st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
                st.stop()
            report = []
            if not os.path.exists("base.db"):
                st.error("No se encontró base.db en el directorio principal")
                st.stop()
            file_id = backup_storage.subir_backup("base.db")
            report.append(f"📤 Subida OK → ID: {file_id}")
            backups = backup_storage.listar_backups()
            if backups:
                report.append(f"📋 Listado OK → {len(backups)} backups encontrados")
            else:
                report.append("❌ Listado vacío")
            backup_storage.rotar_backups(max_backups=5)
            report.append("♻️ Rotación OK (máx. 5 backups)")
            if backups:
                file_id = backups[0]["id"]
                if os.path.exists("base.db"):
                    if os.path.exists("base.db.bak"):
                        os.remove("base.db.bak")
                    os.rename("base.db", "base.db.bak")
                backup_storage.descargar_backup(file_id, "base.db")
                report.append(f"📥 Restauración OK → {backups[0]['name']} descargado")
            st.success("Validación completada")
            for line in report:
                st.write(line)
        except Exception as e:
            st.error(f"Error en validación CRUD: {e}")

    # Dashboard visual
    st.subheader("📊 Dashboard de Backups en Drive")
    try:
        service = backup_storage._get_service()
        if service is None:
            st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
            st.stop()
        backups = backup_storage.listar_backups(max_results=20)
        if backups:
            import pandas as pd
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
            opciones = {f"{b['name']} ({b['createdTime']})": b['id'] for b in backups}
            seleccion = st.selectbox("Selecciona un backup para acción:", list(opciones.keys()))
            file_id = opciones[seleccion]
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Restaurar seleccionado", key="restore_btn"):
                    try:
                        if os.path.exists("base.db"):
                            if os.path.exists("base.db.bak"):
                                os.remove("base.db.bak")
                            os.rename("base.db", "base.db.bak")
                        backup_storage.descargar_backup(file_id, "base.db")
                        st.success("Backup restaurado en base.db (copia previa en base.db.bak)")
                    except Exception as e:
                        if os.path.exists("base.db.bak"):
                            os.rename("base.db.bak", "base.db")
                        st.error(f"Error en restauración, se recuperó la copia local: {e}")
            with col2:
                confirmar = st.checkbox("Confirmar eliminación", key="confirm_delete")
                if st.button("🗑️ Eliminar seleccionado", key="delete_btn"):
                    if confirmar:
                        service.files().delete(fileId=file_id).execute()
                        st.warning(f"Backup eliminado: {seleccion}")
                    else:
                        st.info("Marca la casilla de confirmación antes de eliminar.")
        else:
            st.info("No hay backups en la carpeta.")
    except Exception as e:
        st.error(f"Error al cargar dashboard de backups: {e}")
    
elif opcion == "🔍 Auditoría":
    st.title("🔍 Auditoría")
    service = backup_storage._get_service()
    if service is None:
        st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
        st.stop()
    auditoria.mostrar_auditoria()

elif opcion == "📈 Historial de Validaciones":
    st.title("📈 Historial de Validaciones")
    service = backup_storage._get_service()
    if service is None:
        st.info("No hay credenciales válidas. Autoriza Google Drive con el enlace mostrado arriba.")
        st.stop()
    historial_validaciones.mostrar_historial()

