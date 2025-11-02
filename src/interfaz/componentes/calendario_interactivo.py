import streamlit as st
from streamlit_calendar import calendar
import datetime
from src.persistencia import sql

# Estilos por tipo de evento
EVENT_STYLES = {
    "sintomas": {"icon": "🩸", "bg": "#FDE2E2", "border": "#EF4444", "text": "#7A1D1D", "priority": 3},
    "menstruacion": {"icon": "🩸", "bg": "#FEE2E2", "border": "#DC2626", "text": "#7A1D1D", "priority": 3},
    "ovulacion": {"icon": "🔄", "bg": "#F3E8FF", "border": "#8B5CF6", "text": "#2E1065", "priority": 3},
    "estado": {"icon": "🧍", "bg": "#E8F6EF", "border": "#22C55E", "text": "#0B4E2E", "priority": 2},
    "altitud": {"icon": "⛰️", "bg": "#E6F0FF", "border": "#3B82F6", "text": "#0B3A82", "priority": 2},
    "respiratorio": {"icon": "🌬️", "bg": "#E0F7FA", "border": "#0EA5E9", "text": "#065F46", "priority": 2},
    "calor": {"icon": "🔥", "bg": "#FFF4E5", "border": "#F97316", "text": "#7C2D12", "priority": 2},
    "cita_test": {"icon": "📅", "bg": "#E2E8F0", "border": "#64748B", "text": "#1E293B", "priority": 4},
    "competicion": {"icon": "🏆", "priority": 1},  # colores dinámicos
    "lesion": {"icon": "🤕", "bg": "#FFF4D6", "border": "#F59E0B", "text": "#7A4B00", "priority": 1},
    "nota": {"icon": "📝", "bg": "#F9FAFB", "border": "#6B7280", "text": "#374151", "priority": 5},
}
def mostrar_calendario_interactivo(eventos, id_atleta):
    """
    Renderiza un calendario interactivo tipo TrainingPeaks usando streamlit-calendar.
    - eventos: lista de diccionarios con al menos 'Fecha' y otros campos.
    - id_atleta: necesario para registrar nuevos estados diarios.
    """

    st.markdown("### 🗓️ Calendario interactivo")

    # Construcción de eventos agrupados por día
    fc_events = []
    for ev in eventos:
        fecha = ev.get("Fecha")
        if not fecha:
            continue

        # Recoger iconos activos
        icons = []
        details = {}
        for key, tipo in [
            ("Síntomas", "sintomas"),
            ("Menstruacion", "menstruacion"),
            ("Ovulacion", "ovulacion"),
            ("Altitud", "altitud"),
            ("Respiratorio", "respiratorio"),
            ("Calor", "calor"),
            ("Cita_test", "cita_test"),
            ("Competición", "competicion"),
            ("Lesión", "lesion"),
            ("Comentario", "nota"),
        ]:
            val = ev.get(key)
            if val and val not in ["-", "No", "Ninguno", None]:
                icons.append(EVENT_STYLES[tipo]["icon"])
                details[key] = val

        # Clasificación de iconos en tres líneas
        ciclo_icons = []
        entreno_icons = []
        resto_icons = []
        for k, t in [("Síntomas","sintomas"),("Menstruacion","menstruacion"),("Ovulacion","ovulacion")]:
            if k in details: ciclo_icons.append(EVENT_STYLES[t]["icon"])
        for k, t in [("Altitud","altitud"),("Respiratorio","respiratorio"),("Calor","calor")]:
            if k in details: entreno_icons.append(EVENT_STYLES[t]["icon"])
        for k, t in [("Competición","competicion"),("Lesión","lesion"),("Cita_test","cita_test"),("Comentario","nota")]:
            if k in details: resto_icons.append(EVENT_STYLES[t]["icon"])

        title = "🧍 Estado diario"
        lines = []
        if ciclo_icons:
            lines.append(" ".join(ciclo_icons))
        if entreno_icons:
            lines.append(" ".join(entreno_icons))
        if resto_icons:
            lines.append(" ".join(resto_icons))
        if lines:
            # Usamos <br> para saltos de línea en HTML
            title += "<br>" + "<br>".join(lines)

        fc_events.append({
            "title": title,
            "start": fecha,
            "allDay": True,
            "backgroundColor": EVENT_STYLES["estado"]["bg"],
            "borderColor": EVENT_STYLES["estado"]["border"],
            "textColor": EVENT_STYLES["estado"]["text"],
            "extendedProps": details
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
        "height": "auto",
        "eventDisplay": "block",
        "dayMaxEventRows": False,  # permitir que la fila crezca según eventos
        # 👇 clave: reescribir el HTML del evento para respetar <br>
        "eventDidMount": """function(info) {
            info.el.innerHTML = info.event.title;
        }"""
    }

    # Renderizar calendario (ahora <br> se interpreta como salto de línea)
    cal = calendar(events=fc_events, options=calendar_options)

    # Mostrar detalles en un modal al hacer clic en un evento
    if cal and "eventClick" in cal:
        props = cal["eventClick"]["event"].get("extendedProps", {})
        if props:
            @st.dialog("📋 Detalles del estado diario")
            def mostrar_detalles():
                st.markdown("### 🩸 Datos de ciclo")
                for k in ["Síntomas","Menstruacion","Ovulacion"]:
                    if props.get(k):
                        st.write(f"- **{k}**: {props[k]}")

                st.markdown("### ⛰️ Condiciones de entrenamiento")
                for k in ["Altitud","Respiratorio","Calor"]:
                    if props.get(k):
                        st.write(f"- **{k}**: {props[k]}")

                st.markdown("### 📌 Otros")
                for k in ["Competición","Lesión","Cita_test","Comentario"]:
                    if props.get(k):
                        st.write(f"- **{k}**: {props[k]}")

            mostrar_detalles()

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
