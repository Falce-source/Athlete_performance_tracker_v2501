import streamlit as st
from streamlit_calendar import calendar
import datetime
from src.persistencia import sql

def mostrar_calendario_interactivo(eventos, id_atleta):
    """
    Renderiza un calendario interactivo tipo TrainingPeaks usando streamlit-calendar.
    - eventos: lista de diccionarios con al menos 'Fecha' y otros campos.
    - id_atleta: necesario para registrar nuevos estados diarios.
    """

    st.markdown("### 🗓️ Calendario interactivo")

    # Transformar tus eventos a formato FullCalendar
    fc_events = []
    for ev in eventos:
        fecha = ev.get("Fecha")
        if not fecha:
            continue
        title_parts = []
        if ev.get("Síntomas") and ev["Síntomas"] != "-":
            title_parts.append(f"🧍 {ev['Síntomas']}")
        if ev.get("Menstruacion") and ev["Menstruacion"] != "-":
            title_parts.append(f"🩸 {ev['Menstruacion']}")
        if ev.get("Ovulacion") and ev["Ovulacion"] != "-":
            title_parts.append(f"🔄 {ev['Ovulacion']}")
        if ev.get("Lesión") and ev["Lesión"] != "-":
            title_parts.append(f"🤕 {ev['Lesión']}")
        if ev.get("Competición"):
            title_parts.append(f"🏆 {ev['Competición']}")
        if ev.get("Tipo") == "sesion":
            title_parts.append(f"🏃 {ev.get('Sesion_tipo','')}")

        fc_events.append({
            "title": " | ".join(title_parts) if title_parts else ev.get("Tipo","Evento"),
            "start": fecha,
            "allDay": True
        })

    # Configuración del calendario
    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek"
        },
        "editable": False,
        "selectable": True,
        "navLinks": True,
        "height": "auto"
    }

    # Renderizar calendario
    cal = calendar(events=fc_events, options=calendar_options)

    # Si el usuario hace click en un día
    if cal and "dateClick" in cal:
        fecha_sel = cal["dateClick"]["date"]
        st.session_state["fecha_seleccionada"] = fecha_sel

    # Mostrar formulario emergente si hay fecha seleccionada
    if "fecha_seleccionada" in st.session_state:
        st.markdown("---")
        st.subheader(f"➕ Registrar estado diario para {st.session_state['fecha_seleccionada']}")
        with st.form("form_estado_diario_popup", clear_on_submit=True):
            sintomas = st.selectbox("Síntomas menstruales", ["Ninguno","Dolor leve","Dolor moderado","Dolor intenso"])
            menstruacion = st.selectbox("Menstruación", ["No","Día 1","Día 2","Día 3","Día 4+"])
            ovulacion = st.selectbox("Ovulación", ["No","Estimada","Confirmada"])
            altitud = st.checkbox("⛰️ Entrenamiento en altitud")
            respiratorio = st.checkbox("🌬️ Entrenamiento respiratorio")
            calor = st.checkbox("🔥 Entrenamiento en calor")
            comentario = st.text_area("📝 Comentario opcional")

            submitted = st.form_submit_button("Guardar estado")
            if submitted:
                sql.crear_evento_calendario(
                    id_atleta=id_atleta,
                    fecha=datetime.datetime.fromisoformat(st.session_state["fecha_seleccionada"]),
                    tipo_evento="estado_diario",
                    valor={
                        "sintomas": sintomas,
                        "menstruacion": menstruacion,
                        "ovulacion": ovulacion,
                        "altitud": altitud,
                        "respiratorio": respiratorio,
                        "calor": calor,
                        "comentario_extra": comentario
                    },
                    notas=None
                )
                st.success("✅ Estado diario registrado correctamente")
                del st.session_state["fecha_seleccionada"]