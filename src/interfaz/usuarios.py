import streamlit as st
import pandas as pd
from src.persistencia import sql
from datetime import datetime
import os

def mostrar_usuarios():
    st.header("👥 Gestión de Usuarios")

    # ───────────────────────────────
    # Información de depuración
    # ───────────────────────────────
    try:
        ruta_db = os.path.abspath(sql.engine.url.database)
        num_usuarios = len(sql.obtener_usuarios())
        st.info(f"🛠️ Base de datos activa: {ruta_db}")
        st.info(f"👥 Número de usuarios actuales: {num_usuarios}")
    except Exception as e:
        st.warning(f"No se pudo obtener información de depuración: {e}")

    # ───────────────────────────────
    # Formulario para crear usuario
    # ───────────────────────────────
    with st.form("form_crear_usuario", clear_on_submit=True):
        st.subheader("➕ Crear nuevo usuario")

        nombre = st.text_input("Nombre", "")
        email = st.text_input("Email", "")
        rol = st.selectbox("Rol", ["admin", "entrenadora", "atleta"])

        submitted = st.form_submit_button("Guardar usuario")

        if submitted:
            if nombre.strip() == "" or email.strip() == "":
                st.error("El nombre y el email son obligatorios")
            else:
                usuario = sql.crear_usuario(nombre=nombre, email=email, rol=rol)
                st.success(f"✅ Usuario '{usuario.nombre}' creado correctamente")

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
        "Creado en": u.creado_en.strftime("%Y-%m-%d %H:%M") if isinstance(u.creado_en, datetime) else str(u.creado_en)
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
    seleccion = st.selectbox("Selecciona un usuario para ver detalles", list(opciones.keys()))

    if seleccion:
        id_usuario = opciones[seleccion]
        usuario = next(u for u in usuarios if u.id_usuario == id_usuario)

        st.markdown(f"""
        ### 📝 Detalles del usuario
        - **ID:** {usuario.id_usuario}
        - **Nombre:** {usuario.nombre}
        - **Email:** {usuario.email}
        - **Rol:** {usuario.rol}
        - **Creado en:** {usuario.creado_en}
        """)

        # ───────────────────────────────
        # Formulario de edición
        # ───────────────────────────────
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

        # ───────────────────────────────
        # Botón de eliminación
        # ───────────────────────────────
        if st.button(f"🗑️ Eliminar usuario '{usuario.nombre}'", type="primary"):
            sql.borrar_usuario(usuario.id_usuario)
            st.warning(f"Usuario '{usuario.nombre}' eliminado correctamente. 🔄 Recarga la página para actualizar la lista.")
        