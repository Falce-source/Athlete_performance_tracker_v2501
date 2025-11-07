import streamlit as st
from datetime import datetime, UTC
import pandas as pd
from src.persistencia import sql

def mostrar_eventos():
    st.header("📅 Gestión de Eventos")

    # ───────────────────────────────
    # Selección de atleta
    # ───────────────────────────────
    atletas = sql.obtener_atletas()
    if not atletas:
        st.info("No hay atletas registrados todavía")
        return

    opciones = {f"{a.nombre} {a.apellidos or ''} (ID {a.id_atleta})": a.id_atleta for a in atletas}
    seleccion = st.selectbox("Selecciona un atleta", list(opciones.keys()))
    id_atleta = opciones[seleccion]
    atleta = sql.obtener_atleta_por_id(id_atleta)

    st.markdown(f"""
    ### 🧭 Atleta seleccionado
    - **ID:** {atleta.id_atleta}
    - **Nombre:** {atleta.nombre} {atleta.apellidos or ""}
    - **Deporte:** {atleta.deporte or "—"}
    - **Nivel:** {atleta.nivel or "—"}
    """)

    st.markdown("---")

    # ───────────────────────────────
    # Formulario para crear evento
    # ───────────────────────────────
    with st.form("form_crear_evento", clear_on_submit=True):
        st.subheader("➕ Crear nuevo evento")

        titulo = st.text_input("Título", "")
        descripcion = st.text_area("Descripción", "")
        fecha = st.date_input("Fecha", datetime.now(UTC).date())
        hora = st.time_input("Hora", datetime.now(UTC).time())
        lugar = st.text_input("Lugar", "")
        tipo = st.selectbox("Tipo", ["Entrenamiento", "Competición", "Revisión médica", "Otro"])

        submitted = st.form_submit_button("Guardar evento")

        if submitted:
            if titulo.strip() == "":
                st.error("El título es obligatorio")
            else:
                # Combinar fecha y hora con zona UTC explícita
                fecha_hora = datetime(
                    year=fecha.year,
                    month=fecha.month,
                    day=fecha.day,
                    hour=hora.hour,
                    minute=hora.minute,
                    second=hora.second,
                    tzinfo=UTC,
                )
                evento = sql.crear_evento(
                    id_atleta=id_atleta,
                    titulo=titulo,
                    descripcion=descripcion,
                    fecha=fecha_hora,
                    lugar=lugar,
                    tipo=tipo,
                )
                st.success(f"✅ Evento '{evento.titulo}' creado correctamente")

    st.markdown("---")

    # ───────────────────────────────
    # Tabla de eventos del atleta
    # ───────────────────────────────
    st.subheader("📋 Eventos del atleta")

    eventos = sql.obtener_eventos_por_atleta(id_atleta)
    if not eventos:
        st.info("Este atleta no tiene eventos registrados todavía")
        return

    df = pd.DataFrame([{
        "ID": e.id_evento,
        "Título": e.titulo,
        "Descripción": e.descripcion,
        "Fecha": e.fecha.strftime("%Y-%m-%d %H:%M"),
        "Lugar": e.lugar,
        "Tipo": e.tipo,
    } for e in eventos])

    # Filtros simples por tipo
    tipos = ["Todos"] + sorted([t for t in df["Tipo"].dropna().unique().tolist()])
    tipo_filtro = st.selectbox("Filtrar por tipo", tipos)

    df_filtrado = df.copy()
    if tipo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_filtro]

    st.dataframe(df_filtrado, width='stretch')

    # ───────────────────────────────
    # Detalle de evento + eliminación
    # ───────────────────────────────
    opciones_evento = {f"{row['Título']} ({row['Fecha']}) [ID {row['ID']}]" : int(row["ID"]) for _, row in df_filtrado.iterrows()}
    if opciones_evento:
        seleccion_evento = st.selectbox("Selecciona un evento para ver detalles", list(opciones_evento.keys()))
        id_evento = opciones_evento[seleccion_evento]
        evento = next(e for e in eventos if e.id_evento == id_evento)

        st.markdown(f"""
        ### 📝 Detalles del evento
        - **ID:** {evento.id_evento}
        - **Título:** {evento.titulo}
        - **Descripción:** {evento.descripcion or "—"}
        - **Fecha:** {evento.fecha.strftime("%Y-%m-%d %H:%M")}
        - **Lugar:** {evento.lugar or "—"}
        - **Tipo:** {evento.tipo or "—"}
        """)

        if st.button(f"🗑️ Eliminar evento '{evento.titulo}'", type="primary"):
            sql.borrar_evento(evento.id_evento)
            st.warning(f"Evento '{evento.titulo}' eliminado correctamente. 🔄 Recarga la página para actualizar la lista.")