import streamlit as st
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
    # Selector de atletas existentes
    # ───────────────────────────────
    st.subheader("📋 Atletas registrados")

    atletas = sql.obtener_atletas()
    if not atletas:
        st.info("No hay atletas registrados todavía")
        return

    opciones = {f"{a.nombre} {a.apellidos or ''} (ID {a.id_atleta})": a.id_atleta for a in atletas}
    seleccion = st.selectbox("Selecciona un atleta", list(opciones.keys()))

    if seleccion:
        id_atleta = opciones[seleccion]
        atleta = sql.obtener_atleta_por_id(id_atleta)

        st.write("### Datos del atleta")
        st.json({
            "ID": atleta.id_atleta,
            "Nombre": atleta.nombre,
            "Apellidos": atleta.apellidos,
            "Edad": atleta.edad,
            "Talla": atleta.talla,
            "Contacto": atleta.contacto,
            "Deporte": atleta.deporte,
            "Modalidad": atleta.modalidad,
            "Nivel": atleta.nivel,
            "Equipo": atleta.equipo,
            "Alergias": atleta.alergias,
            "Consentimiento": atleta.consentimiento,
            "Creado en": str(atleta.creado_en),
        })