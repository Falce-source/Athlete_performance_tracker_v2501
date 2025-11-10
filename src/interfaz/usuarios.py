import streamlit as st
import pandas as pd
import src.persistencia.sql as sql
from datetime import datetime
from src.utils.seguridad import hash_password

def mostrar_usuarios(rol_actual: str, usuario_id: int):
    st.header("👥 Gestión de Usuarios")

    # ───────────────────────────────
    # Información de depuración extendida (solo admin)
    # ───────────────────────────────
    if rol_actual == "admin":
        import os
        import src.persistencia.backup_storage as backup_storage

        try:
            ruta_db = os.path.abspath(sql.engine.url.database)
            num_usuarios = len(sql.obtener_usuarios())
            num_atletas = len(sql.obtener_atletas())
            num_eventos = len(sql.obtener_eventos())

            backups = backup_storage.listar_backups()
            if backups:
                ultimo = sorted(backups, key=lambda b: b["createdTime"], reverse=True)[0]
                fecha_backup = ultimo["createdTime"]
                nombre_backup = ultimo["name"]
                backup_info = f"📦 Último backup: {nombre_backup} ({fecha_backup})"
            else:
                backup_info = "⚠️ No hay backups en Drive"

            st.info(f"🛠️ Base de datos activa: {ruta_db}")
            st.info(f"👥 Usuarios: {num_usuarios} | 🏃‍♂️ Atletas: {num_atletas} | 📅 Eventos: {num_eventos}")
            st.info(backup_info)

        except Exception as e:
            st.warning(f"No se pudo obtener información de depuración: {e}")

    # ───────────────────────────────
    # Formulario para crear usuario (solo admin)
    # ───────────────────────────────
    if rol_actual == "admin":
        with st.form("form_crear_usuario", clear_on_submit=True):
            st.subheader("➕ Crear nuevo usuario")

            nombre = st.text_input("Nombre", "")
            email = st.text_input("Email", "")
            rol = st.selectbox("Rol", ["admin", "entrenadora", "atleta"])

            # Campo de contraseña inicial
            password = st.text_input("Contraseña inicial", type="password")

            # 🔑 Si el rol es atleta, solo se crea el usuario login.
            # El perfil atleta lo crea después la entrenadora y se vincula.
            if rol == "atleta":
                st.info("ℹ️ Recuerda: el perfil atleta será creado posteriormente por la entrenadora y vinculado a este usuario.")

            submitted = st.form_submit_button("Guardar usuario")

            if submitted:
                if nombre.strip() == "" or email.strip() == "" or password.strip() == "":
                    st.error("Nombre, email y contraseña son obligatorios")
                else:
                    ph = hash_password(password)
                    usuario = sql.crear_usuario(nombre=nombre, email=email, rol=rol, password_hash=ph)
                    st.success(f"✅ Usuario '{usuario.nombre}' creado correctamente con contraseña inicial")

                    # 🔑 Si es atleta, no se crea perfil aquí.
                    # El perfil será creado por la entrenadora y luego vinculado.
                    if rol == "atleta":
                        st.info("🔗 Usuario atleta creado. Pendiente de asociación con perfil.")

    st.markdown("---")

    # ───────────────────────────────
    # Tabla de usuarios con filtros
    # ───────────────────────────────
    st.subheader("📋 Usuarios registrados")

    usuarios = sql.obtener_usuarios()
    if not usuarios:
        st.info("No hay usuarios registrados todavía")
        return

    df = pd.DataFrame([{
        "ID": u.id_usuario,
        "Nombre": u.nombre,
        "Email": u.email,
        "Rol": u.rol,
        "Creado en": u.creado_en.strftime("%Y-%m-%d %H:%M") if isinstance(u.creado_en, datetime) else str(u.creado_en),
        # 🔑 Si es atleta, buscamos su perfil y mostramos entrenadora asignada
        "Entrenadora asignada": (
            next((a.usuario.nombre for a in sql.obtener_atletas() if getattr(a, "atleta_usuario_id", None) == u.id_usuario and a.usuario), "—")
            if u.rol == "atleta" else "—"
        )
    } for u in usuarios])

    rol_filtro = st.selectbox("Filtrar por rol", ["Todos"] + sorted(df["Rol"].dropna().unique().tolist()))
    df_filtrado = df.copy()
    if rol_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Rol"] == rol_filtro]

    st.dataframe(df_filtrado, width="stretch")

    # ───────────────────────────────
    # Selector de usuario individual + edición/eliminación
    # ───────────────────────────────
    opciones = {f"{u.nombre} ({u.email}) - {u.rol} (ID {u.id_usuario})": u.id_usuario for u in usuarios}
    if opciones:
        seleccion = st.selectbox("Selecciona un usuario para ver detalles", list(opciones.keys()))
        if seleccion:
            id_usuario = opciones.get(seleccion)  # 🔑 usar .get() evita KeyError
            if id_usuario is not None:
                usuario = next(u for u in usuarios if u.id_usuario == id_usuario)

                st.markdown(f"""
                ### 📝 Detalles del usuario
                - **ID:** {usuario.id_usuario}
                - **Nombre:** {usuario.nombre}
                - **Email:** {usuario.email}
                - **Rol:** {usuario.rol}
                - **Creado en:** {usuario.creado_en}
                {"- **Entrenadora asignada:** " + next((a.usuario.nombre for a in sql.obtener_atletas() if getattr(a, "propietario_id", None) == usuario.id_usuario and a.usuario), "—") if usuario.rol == "atleta" else ""}
                """)
    else:
        st.info("No hay usuarios disponibles para seleccionar.")

    # ───────────────────────────────
    # Formulario de edición y eliminación (solo admin)
    # ───────────────────────────────
    if rol_actual == "admin" and opciones and seleccion:
        with st.expander("✏️ Editar usuario"):
            with st.form(f"form_editar_{id_usuario}"):
                nuevo_nombre = st.text_input("Nombre", usuario.nombre)
                nuevo_email = st.text_input("Email", usuario.email)
                nuevo_rol = st.selectbox("Rol", ["admin", "entrenadora", "atleta"],
                                         index=["admin","entrenadora","atleta"].index(usuario.rol))

                # Campo opcional para resetear contraseña
                nueva_password = st.text_input("Nueva contraseña (dejar vacío si no quieres cambiarla)", type="password")
                actualizar = st.form_submit_button("💾 Guardar cambios")

                if actualizar:
                    try:
                        if nueva_password.strip():
                            ph = hash_password(nueva_password)
                            sql.actualizar_usuario(
                                id_usuario=usuario.id_usuario,
                                nombre=nuevo_nombre,
                                email=nuevo_email,
                                rol=nuevo_rol,
                                password_hash=ph
                            )
                            st.success(f"✅ Usuario '{nuevo_nombre}' actualizado y contraseña reseteada. 🔄 Recarga la página para ver los cambios.")
                        else:
                            sql.actualizar_usuario(
                                id_usuario=usuario.id_usuario,
                                nombre=nuevo_nombre,
                                email=nuevo_email,
                                rol=nuevo_rol
                            )
                            st.success(f"✅ Usuario '{nuevo_nombre}' actualizado correctamente. 🔄 Recarga la página para ver los cambios.")
                    except ValueError as e:
                        st.error(str(e))

        if st.button(f"🗑️ Eliminar usuario '{usuario.nombre}'", type="primary"):
            try:
                sql.borrar_usuario(usuario.id_usuario)
                st.warning(f"Usuario '{usuario.nombre}' eliminado correctamente. 🔄 Recarga la página para actualizar la lista.")
            except ValueError as e:
                st.error(str(e))
        