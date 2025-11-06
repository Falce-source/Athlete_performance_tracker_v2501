import streamlit as st
import pandas as pd
from src.persistencia import sql
from datetime import datetime
from src.utils.seguridad import hash_password

def mostrar_usuarios(rol_actual: str, usuario_id: int):
    st.header("👥 Gestión de Usuarios")

    # ───────────────────────────────
    # Información de depuración extendida
    # ───────────────────────────────
    import os
    from src.persistencia import sql
    import backup_storage

    try:
        ruta_db = os.path.abspath(sql.engine.url.database)
        num_usuarios = len(sql.obtener_usuarios())
        num_atletas = len(sql.obtener_atletas())
        num_eventos = len(sql.obtener_eventos())

        # Último backup en Drive
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

            # 🔑 Si el rol es atleta, mostrar subformulario de perfil
            if rol == "atleta":
                nombre_atleta = st.text_input("Nombre atleta", "")
                apellidos_atleta = st.text_input("Apellidos", "")
                edad_atleta = st.number_input("Edad", min_value=0, max_value=120, step=1)
                deporte_atleta = st.text_input("Deporte", "")
                nivel_atleta = st.selectbox("Nivel", ["Iniciado", "Intermedio", "Avanzado", "Elite"])

                # Admin asigna entrenadora
                usuarios = sql.obtener_usuarios()
                entrenadoras = [u for u in usuarios if u.rol == "entrenadora"]
                opciones_entrenadora = {f"{e.nombre} (ID {e.id_usuario})": e.id_usuario for e in entrenadoras}
                seleccion_entrenadora = st.selectbox("Asignar entrenadora", list(opciones_entrenadora.keys()))
                id_entrenadora = opciones_entrenadora[seleccion_entrenadora]

            submitted = st.form_submit_button("Guardar usuario")

            if submitted:
                if nombre.strip() == "" or email.strip() == "" or password.strip() == "":
                    st.error("Nombre, email y contraseña son obligatorios")
                else:
                    ph = hash_password(password)
                    usuario = sql.crear_usuario(nombre=nombre, email=email, rol=rol, password_hash=ph)
                    st.success(f"✅ Usuario '{usuario.nombre}' creado correctamente con contraseña inicial")

                    # 🔑 Si es atleta, crear también perfil vinculado
                    if rol == "atleta":
                        atleta = sql.crear_atleta(
                            nombre=nombre_atleta,
                            apellidos=apellidos_atleta,
                            edad=int(edad_atleta) if edad_atleta else None,
                            deporte=deporte_atleta,
                            nivel=nivel_atleta,
                            id_usuario=id_entrenadora,
                            propietario_id=usuario.id_usuario
                        )
                        st.success(f"✅ Perfil de atleta '{atleta.nombre}' creado y vinculado a entrenadora.")

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
            next((a.usuario.nombre for a in sql.obtener_atletas() if getattr(a, "propietario_id", None) == u.id_usuario and a.usuario), "—")
            if u.rol == "atleta" else "—"
        )
    } for u in usuarios])

    rol_filtro = st.selectbox("Filtrar por rol", ["Todos"] + sorted(df["Rol"].dropna().unique().tolist()))
    df_filtrado = df.copy()
    if rol_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Rol"] == rol_filtro]

    st.dataframe(df_filtrado, use_container_width=True)

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
        if rol_actual == "admin":
            with st.expander("✏️ Editar usuario"):
                with st.form(f"form_editar_{id_usuario}"):
                    nuevo_nombre = st.text_input("Nombre", usuario.nombre)
                    nuevo_email = st.text_input("Email", usuario.email)
                    nuevo_rol = st.selectbox("Rol", ["admin", "entrenadora", "atleta"],
                                             index=["admin","entrenadora","atleta"].index(usuario.rol))

                    actualizar = st.form_submit_button("💾 Guardar cambios")

                    if actualizar:
                        sql.actualizar_usuario(
                            id_usuario=usuario.id_usuario,
                            nombre=nuevo_nombre,
                            email=nuevo_email,
                            rol=nuevo_rol
                        )
                        st.success(f"✅ Usuario '{nuevo_nombre}' actualizado correctamente. 🔄 Recarga la página para ver los cambios.")

            if st.button(f"🗑️ Eliminar usuario '{usuario.nombre}'", type="primary"):
                sql.borrar_usuario(usuario.id_usuario)
                st.warning(f"Usuario '{usuario.nombre}' eliminado correctamente. 🔄 Recarga la página para actualizar la lista.")
        