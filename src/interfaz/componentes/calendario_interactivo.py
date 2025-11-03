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

        # Evento principal: cabecera "Estado diario"
        fc_events.append({
            "title": "🧍 Estado diario",
            "start": fecha,
            "allDay": True,
            "backgroundColor": EVENT_STYLES["estado"]["bg"],
            "borderColor": EVENT_STYLES["estado"]["border"],
            "textColor": EVENT_STYLES["estado"]["text"],
            "extendedProps": {**details, "displayOrder": 0}
        })

        # Evento auxiliar: ciclo
        if ciclo_icons:
            fc_events.append({
                "title": " ".join(ciclo_icons),
                "start": fecha,
                "allDay": True,
                "backgroundColor": "transparent",
                "borderColor": "transparent",
                "textColor": EVENT_STYLES["estado"]["text"],
                "extendedProps": {**details, "displayOrder": 1}
            })

        # Evento auxiliar: entreno
        if entreno_icons:
            fc_events.append({
                "title": " ".join(entreno_icons),
                "start": fecha,
                "allDay": True,
                "backgroundColor": "transparent",
                "borderColor": "transparent",
                "textColor": EVENT_STYLES["estado"]["text"],
                "extendedProps": {**details, "displayOrder": 2}
            })

        # Evento auxiliar: resto
        if resto_icons:
            fc_events.append({
                "title": " ".join(resto_icons),
                "start": fecha,
                "allDay": True,
                "backgroundColor": "transparent",
                "borderColor": "transparent",
                "textColor": EVENT_STYLES["estado"]["text"],
                "extendedProps": {**details, "displayOrder": 3}
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
        "dayMaxEventRows": True,
        "eventOrder": "displayOrder"
    }

    # CSS para compactar las filas de eventos
    st.markdown("""
    <style>
    .fc-daygrid-event {
        margin: 0 !important;
        padding: 0 !important;
    }
    .fc-daygrid-event .fc-event-title {
        line-height: 1.2em !important;
        white-space: nowrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Renderizar calendario (ahora \n se interpreta como salto de línea)
    cal = calendar(events=fc_events, options=calendar_options)

    # Modal editable al hacer clic en la cabecera
    if cal and "eventClick" in cal:
        ev = cal["eventClick"]["event"]
        props = ev.get("extendedProps", {})
        if props and props.get("displayOrder") == 0:
            @st.dialog("📋 Editar estado diario")
            def editar_estado():
                with st.form("form_editar_estado", clear_on_submit=True):
                    sintomas = st.selectbox("Síntomas menstruales",
                        ["Ninguno","Dolor leve","Dolor moderado","Dolor intenso"],
                        index=["Ninguno","Dolor leve","Dolor moderado","Dolor intenso"].index(props.get("Síntomas","Ninguno")))
                    menstruacion = st.selectbox("Menstruación",
                        ["No","Día 1","Día 2","Día 3","Día 4+"],
                        index=["No","Día 1","Día 2","Día 3","Día 4+"].index(props.get("Menstruacion","No")))
                    ovulacion = st.selectbox("Ovulación",
                        ["No","Estimada","Confirmada"],
                        index=["No","Estimada","Confirmada"].index(props.get("Ovulacion","No")))

                    altitud = st.checkbox("⛰️ Entrenamiento en altitud", value=bool(props.get("Altitud")))
                    respiratorio = st.checkbox("🌬️ Entrenamiento respiratorio", value=bool(props.get("Respiratorio")))
                    calor = st.checkbox("🔥 Entrenamiento en calor", value=bool(props.get("Calor")))

                    cita_test = st.selectbox("📅 Citas / Tests", ["No","Cita","Test"],
                        index=["No","Cita","Test"].index(props.get("Cita_test","No")))
                    fecha_competicion = st.date_input("🏆 Fecha de competición",
                        value=datetime.date.fromisoformat(props.get("fecha_competicion")) if props.get("fecha_competicion") else None)
                    lesion = st.text_input("🤕 Lesión", value=props.get("Lesión",""))
                    comentario_extra = st.text_area("📝 Notas adicionales", value=props.get("Comentario",""))

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar cambios")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        fecha_dt = datetime.datetime.fromisoformat(ev["start"].replace("Z", "+00:00"))
                        sql.actualizar_evento_calendario(
                            id_atleta=id_atleta,
                            fecha=fecha_dt,
                            valores_actualizados={
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
                            }
                        )
                        st.success("✅ Estado diario actualizado")
                        st.rerun()  # recarga para cerrar modal y refrescar calendario

                    if eliminar:
                        fecha_dt = datetime.datetime.fromisoformat(ev["start"].replace("Z", "+00:00"))
                        sql.borrar_evento_calendario(id_atleta=id_atleta, fecha=fecha_dt)
                        st.success("🗑️ Estado diario eliminado")
                        st.rerun()  # recarga para cerrar modal y refrescar calendario

            editar_estado()

    # Modal de registro al hacer clic en un día vacío
    if cal and "dateClick" in cal:
        fecha_iso = cal["dateClick"].get("dateStr") or cal["dateClick"].get("date")
        # Parseamos el string ISO completo y lo convertimos a zona horaria local
        fecha_dt = datetime.datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))
        fecha_local = fecha_dt.astimezone().date()

        @st.dialog(f"➕ Registrar estado diario para {fecha_local.strftime('%Y-%m-%d')}")
        def registrar_estado():
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
                    fecha_guardar = datetime.datetime.combine(
                        fecha_local,
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

        registrar_estado()
