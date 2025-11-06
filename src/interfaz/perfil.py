import streamlit as st
import pandas as pd
import src.persistencia.sql as sql

# Importar control de roles
from src.utils.roles import Contexto, puede_editar_perfil_atleta

def mostrar_perfil(rol_actual="admin", usuario_id=None):
    st.header("👤 Perfil de Atleta")

    if rol_actual in ["entrenadora", "atleta"]:
        usuarios = sql.obtener_usuarios()
        nombre_usuario = next((u.nombre for u in usuarios if u.id_usuario == usuario_id), "—")
        st.caption(f"🔐 Rol activo: {rol_actual} | Usuario: {nombre_usuario} (ID {usuario_id})")
    elif rol_actual == "admin":
        st.caption("🔐 Rol activo: admin")

    # ───────────────────────────────
    # Información de depuración extendida
    # ───────────────────────────────
    import os
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
    # Formulario para crear atleta (condicionado por rol)
    # ───────────────────────────────
    puede_crear = rol_actual in ["admin", "entrenadora"]

    # Caso especial: atleta puede crear solo su propio perfil si aún no existe
    if rol_actual == "atleta":
        atletas_propios = sql.obtener_atletas_por_usuario(usuario_id)
        if not atletas_propios:   # 🔑 solo si no tiene ninguno
            puede_crear = True
        else:
            # 🔔 Aviso visual si ya tiene perfil
            st.info("Ya tienes un perfil creado. No puedes crear más atletas.")

    if puede_crear:
        with st.form("form_crear_atleta", clear_on_submit=True):
            st.subheader("➕ Crear nuevo atleta")

            # 🔑 Si el rol es admin, elegir entrenadora dentro del formulario
            if rol_actual == "admin":
                usuarios = sql.obtener_usuarios()
                entrenadoras = [u for u in usuarios if u.rol == "entrenadora"]
                opciones_entrenadora = {f"{e.nombre} (ID {e.id_usuario})": e.id_usuario for e in entrenadoras}
                seleccion_entrenadora = st.selectbox("Asignar atleta a entrenadora", list(opciones_entrenadora.keys()))
                id_usuario_asignado = opciones_entrenadora[seleccion_entrenadora]
            else:
                id_usuario_asignado = usuario_id

            # 🔑 admin → entrenadora seleccionada, entrenadora → ella misma, atleta → su propio usuario

            nombre = st.text_input("Nombre", "")
            apellidos = st.text_input("Apellidos", "")
            edad = st.number_input("Edad", min_value=0, max_value=120, step=1)
            talla = st.number_input("Talla (cm)", min_value=100, max_value=250, step=1)
            contacto = st.text_input("Contacto (email/teléfono)", "")
            deporte = st.text_input("Deporte", "")
            modalidad = st.text_input("Modalidad", "")
            nivel = st.selectbox("Nivel", ["Iniciado", "Intermedio", "Avanzado", "Elite"])
            equipo = st.text_input("Equipo", "")
            alergias = st.text_area("Alergias", "")
            consentimiento = st.checkbox("Consentimiento informado")

            submitted = st.form_submit_button("Guardar atleta")

            if submitted:
                if nombre.strip() == "":
                    st.error("El nombre es obligatorio")
                else:
                    atleta = sql.crear_atleta(
                        nombre=nombre,
                        apellidos=apellidos,
                        edad=int(edad) if edad else None,
                        talla=int(talla) if talla else None,
                        contacto=contacto,
                        deporte=deporte,
                        modalidad=modalidad,
                        nivel=nivel,
                        equipo=equipo,
                        alergias=alergias,
                        consentimiento=consentimiento,
                        id_usuario=id_usuario_asignado  # 🔑 admin → entrenadora seleccionada, entrenadora → ella misma, atleta → su propio usuario
                    )
                    st.success(f"✅ Atleta '{atleta.nombre}' creado correctamente")
    else:
        st.caption("⛔ No tienes permisos para crear atletas")

    st.markdown("---")

    # ───────────────────────────────
    # Tabla de atletas con filtros
    # ───────────────────────────────
    st.subheader("📋 Atletas registrados")

    if rol_actual == "entrenadora":
        atletas = sql.obtener_atletas_por_usuario(usuario_id)  # 🔍 solo los suyos

    elif rol_actual == "admin":
        usuarios = sql.obtener_usuarios()
        entrenadoras = [u for u in usuarios if u.rol == "entrenadora"]
        opciones_entrenadora = {f"{e.nombre} (ID {e.id_usuario})": e.id_usuario for e in entrenadoras}
        seleccion_entrenadora = st.selectbox("Filtrar atletas por entrenadora", list(opciones_entrenadora.keys()))
        id_entrenadora = opciones_entrenadora[seleccion_entrenadora]
        # 🔑 obtenemos atletas vinculados a la entrenadora seleccionada con relación usuario cargada
        atletas = sql.obtener_atletas_por_usuario(id_entrenadora)

    else:
        atletas = sql.obtener_atletas()

    if not atletas:
        st.info("No hay atletas registrados todavía")
        return

    df = pd.DataFrame([{
        "ID": a.id_atleta,
        "Nombre": a.nombre,
        "Apellidos": a.apellidos,
        "Edad": a.edad,
        "Deporte": a.deporte,
        "Nivel": a.nivel,
        "Equipo": a.equipo,
        "Entrenadora": a.usuario.nombre if a.usuario else "—"
    } for a in atletas])

    col1, col2 = st.columns(2)
    with col1:
        deporte_filtro = st.selectbox("Filtrar por deporte", ["Todos"] + sorted(df["Deporte"].dropna().unique().tolist()))
    with col2:
        nivel_filtro = st.selectbox("Filtrar por nivel", ["Todos"] + sorted(df["Nivel"].dropna().unique().tolist()))

    df_filtrado = df.copy()
    if deporte_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Deporte"] == deporte_filtro]
    if nivel_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Nivel"] == nivel_filtro]

    st.dataframe(df_filtrado, use_container_width=True)

    # ───────────────────────────────
    # Selector de atleta individual + edición/eliminación
    # ───────────────────────────────
    opciones = {f"{a.nombre} {a.apellidos or ''} (ID {a.id_atleta})": a.id_atleta for a in atletas}
    seleccion = st.selectbox("Selecciona un atleta para ver detalles", list(opciones.keys()))

    if seleccion:
        id_atleta = opciones[seleccion]
        atleta = sql.obtener_atleta_por_id(id_atleta)

        # Construir contexto de permisos para este atleta
        ctx = Contexto(
            rol_actual=rol_actual,
            usuario_id=usuario_id or 0,
            atleta_id=id_atleta,
            propietario_id=atleta.id_usuario if hasattr(atleta, "id_usuario") else None
        )

        st.markdown(f"""
        ### 📝 Detalles del atleta
        - **ID:** {atleta.id_atleta}
        - **Nombre:** {atleta.nombre} {atleta.apellidos or ""}
        - **Edad:** {atleta.edad or "—"}
        - **Talla:** {atleta.talla or "—"} cm
        - **Contacto:** {atleta.contacto or "—"}
        - **Deporte:** {atleta.deporte or "—"}
        - **Modalidad:** {atleta.modalidad or "—"}
        - **Nivel:** {atleta.nivel or "—"}
        - **Equipo:** {atleta.equipo or "—"}
        - **Alergias:** {atleta.alergias or "—"}
        - **Consentimiento:** {"✅ Sí" if atleta.consentimiento else "❌ No"}
        - **Entrenadora asignada:** {atleta.usuario.nombre if atleta.usuario else "—"}
        - **Creado en:** {str(atleta.creado_en)}
        """)

        # ───────────────────────────────
        # Formulario de edición (condicionado por permisos)
        # ───────────────────────────────
        if puede_editar_perfil_atleta(ctx):
            with st.expander("✏️ Editar atleta"):
                with st.form(f"form_editar_{id_atleta}"):
                    nuevo_nombre = st.text_input("Nombre", atleta.nombre)
                    nuevos_apellidos = st.text_input("Apellidos", atleta.apellidos or "")
                    nueva_edad = st.number_input("Edad", min_value=0, max_value=120, step=1, value=atleta.edad or 0)
                    nueva_talla = st.number_input("Talla (cm)", min_value=100, max_value=250, step=1, value=atleta.talla or 170)
                    nuevo_contacto = st.text_input("Contacto", atleta.contacto or "")
                    nuevo_deporte = st.text_input("Deporte", atleta.deporte or "")
                    nueva_modalidad = st.text_input("Modalidad", atleta.modalidad or "")
                    niveles = ["Iniciado", "Intermedio", "Avanzado", "Elite"]
                    nivel_actual = atleta.nivel if atleta.nivel in niveles else None
                    index_nivel = niveles.index(nivel_actual) if nivel_actual else 0
                    nuevo_nivel = st.selectbox("Nivel", niveles, index=index_nivel)
                    nuevo_equipo = st.text_input("Equipo", atleta.equipo or "")
                    nuevas_alergias = st.text_area("Alergias", atleta.alergias or "")
                    nuevo_consentimiento = st.checkbox("Consentimiento informado", value=atleta.consentimiento)

                    actualizar = st.form_submit_button("💾 Guardar cambios")

                    if actualizar:
                        sql.actualizar_atleta(
                            id_atleta=atleta.id_atleta,
                            nombre=nuevo_nombre,
                            apellidos=nuevos_apellidos,
                            edad=int(nueva_edad),
                            talla=int(nueva_talla),
                            contacto=nuevo_contacto,
                            deporte=nuevo_deporte,
                            modalidad=nueva_modalidad,
                            nivel=nuevo_nivel,
                            equipo=nuevo_equipo,
                            alergias=nuevas_alergias,
                            consentimiento=nuevo_consentimiento,
                        )
                        st.success(f"✅ Atleta '{nuevo_nombre}' actualizado correctamente. 🔄 Recarga la página para ver los cambios.")
        else:
            st.caption("⛔ No tienes permisos para editar este perfil")

        # ───────────────────────────────
        # Botón de eliminación (solo admin/entrenadora)
        # ───────────────────────────────
        if puede_editar_perfil_atleta(ctx):
            if st.button(f"🗑️ Eliminar atleta '{atleta.nombre}'", type="primary"):
                sql.borrar_atleta(atleta.id_atleta)
                st.warning(f"Atleta '{atleta.nombre}' eliminado correctamente. 🔄 Recarga la página para actualizar la lista.")
        else:
            st.caption("⛔ No tienes permisos para eliminar este atleta")
