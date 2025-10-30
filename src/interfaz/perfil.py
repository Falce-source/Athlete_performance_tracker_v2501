import streamlit as st
import pandas as pd
from src.persistencia import sql

def mostrar_perfil():
    st.header("👤 Perfil de Atleta")

    # ───────────────────────────────
    # Formulario para crear atleta
    # ───────────────────────────────
    with st.form("form_crear_atleta", clear_on_submit=True):
        st.subheader("➕ Crear nuevo atleta")

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
                )
                st.success(f"✅ Atleta '{atleta.nombre}' creado correctamente")

    st.markdown("---")

    # ───────────────────────────────
    # Tabla de atletas con filtros
    # ───────────────────────────────
    st.subheader("📋 Atletas registrados")

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
        - **Creado en:** {str(atleta.creado_en)}
        """)

        # ───────────────────────────────
        # Formulario de edición
        # ───────────────────────────────
        with st.expander("✏️ Editar atleta"):
            with st.form(f"form_editar_{id_atleta}"):
                nuevo_nombre = st.text_input("Nombre", atleta.nombre)
                nuevos_apellidos = st.text_input("Apellidos", atleta.apellidos or "")
                nueva_edad = st.number_input("Edad", min_value=0, max_value=120, step=1, value=atleta.edad or 0)
                nueva_talla = st.number_input("Talla (cm)", min_value=100, max_value=250, step=1, value=atleta.talla or 170)
                nuevo_contacto = st.text_input("Contacto", atleta.contacto or "")
                nuevo_deporte = st.text_input("Deporte", atleta.deporte or "")
                nueva_modalidad = st.text_input("Modalidad", atleta.modalidad or "")
                nuevo_nivel = st.selectbox("Nivel", ["Iniciado", "Intermedio", "Avanzado", "Elite"], index=["Iniciado","Intermedio","Avanzado","Elite"].index(atleta.nivel) if atleta.nivel else 0)
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

        # ───────────────────────────────
        # Botón de eliminación
        # ───────────────────────────────
        if st.button(f"🗑️ Eliminar atleta '{atleta.nombre}'", type="primary"):
            sql.borrar_atleta(atleta.id_atleta)
            st.warning(f"Atleta '{atleta.nombre}' eliminado correctamente. 🔄 Recarga la página para actualizar la lista.")