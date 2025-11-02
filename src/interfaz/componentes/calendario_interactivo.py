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

    # Transformar eventos a varias líneas por día (apilado vertical nativo)
    fc_events = []
    for ev in eventos:
        fecha = ev.get("Fecha")
        if not fecha:
            continue

        def add_event(line: str):
            fc_events.append({
                "title": line,
                "start": fecha,
                "allDay": True
            })

        if ev.get("Síntomas") and ev["Síntomas"] != "-":
            add_event(f"🧍 Síntomas: {ev['Síntomas']}")
        if ev.get("Menstruacion") and ev["Menstruacion"] != "-":
            add_event(f"🩸 Menstruación: {ev['Menstruacion']}")
        if ev.get("Ovulacion") and ev["Ovulacion"] != "-":
            add_event(f"🔄 Ovulación: {ev['Ovulacion']}")
        if ev.get("Altitud") == "Sí":
            add_event("⛰️ Entrenamiento en altitud")
        if ev.get("Respiratorio") == "Sí":
            add_event("🌬️ Entrenamiento respiratorio")
        if ev.get("Calor") == "Sí":
            add_event("🔥 Entrenamiento en calor")
        if ev.get("Cita_test") and ev["Cita_test"] != "-":
            add_event(f"📅 {ev['Cita_test']}")
        if ev.get("Competición"):
            add_event(f"🏆 {ev['Competición']}")
        if ev.get("Lesión") and ev["Lesión"] != "-":
            add_event(f"🤕 {ev['Lesión']}")
        if ev.get("Comentario") and ev["Comentario"] != "-":
            add_event(f"📝 {ev['Comentario']}")
        # Fallback cuando no hay detalles
        if not any(k in ev for k in ["Síntomas","Menstruacion","Ovulacion","Altitud","Respiratorio","Calor","Cita_test","Competición","Lesión","Comentario"]):
            add_event(ev.get("Tipo", "Evento"))

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
        "height": "auto",
        "eventDisplay": "block"
    }

    # Renderizar calendario
    cal = calendar(events=fc_events, options=calendar_options)

    # Si el usuario hace click en un día (usar dateStr para evitar desfases)
    if cal and "dateClick" in cal:
        fecha_sel = cal["dateClick"].get("dateStr") or cal["dateClick"].get("date")
        st.session_state["fecha_seleccionada"] = fecha_sel

    # Mostrar formulario emergente si hay fecha seleccionada
    if "fecha_seleccionada" in st.session_state:
        st.markdown("---")
        st.subheader(f"➕ Registrar estado diario para {st.session_state['fecha_seleccionada']}")
        with st.form("form_estado_diario_popup", clear_on_submit=True):
            # 1. Datos de ciclo
            with st.expander("🩸 Datos de ciclo"):
                sintomas = st.selectbox("Síntomas menstruales", ["Ninguno","Dolor leve","Dolor moderado","Dolor intenso"])
                menstruacion = st.selectbox("Menstruación", ["No","Día 1","Día 2","Día 3","Día 4+"])
                ovulacion = st.selectbox("Ovulación", ["No","Estimada","Confirmada"])

            # 2-4. Entrenamientos especiales
            altitud = st.checkbox("⛰️ Entrenamiento en altitud")
            respiratorio = st.checkbox("🌬️ Entrenamiento respiratorio")
            calor = st.checkbox("🔥 Entrenamiento en calor")

            # 5. Citas/tests
            with st.expander("📅 Citas / Tests"):
                cita_test = st.selectbox("Selecciona", ["No","Cita","Test"])

            # 6. Competición
            with st.expander("🏆 Competición"):
                fecha_competicion = st.date_input("Fecha de competición", value=None)

            # 7. Lesiones/molestias
            with st.expander("🤕 Lesiones / molestias"):
                lesion = st.text_input("Descripción de la lesión o molestia")

            # 8. Notas adicionales
            with st.expander("📝 Notas adicionales"):
                comentario_extra = st.text_area("Escribe tu comentario")

            submitted = st.form_submit_button("Guardar estado")
            if submitted:
                # Guardar como datetime UTC a medianoche para consistencia
                fecha_guardar = datetime.datetime.combine(
                    datetime.date.fromisoformat(st.session_state["fecha_seleccionada"][:10]),
                    datetime.time.min,
                    tzinfo=datetime.timezone.utc
                )
                sql.crear_evento_calendario(
                    id_atleta=id_atleta,
                    fecha=fecha_guardar,
                     tipo_evento="estado_diario",
                    tipo_evento="estado_diario",
                    valor={
                        "sintomas": sintomas,
                        "menstruacion": menstruacion,
                        "ovulacion": ovulacion,
                        "altitud": altitud,
                        "respiratorio": respiratorio,
                        "calor": calor,
                        "cita_test": cita_test,
                        "fecha_competicion": str(fecha_competicion) if fecha_competicion else None,
                        "lesion": lesion,
                        "comentario_extra": comentario_extra
                    },
                    notas=None
                )
                st.success("✅ Estado diario registrado correctamente")
                del st.session_state["fecha_seleccionada"]
