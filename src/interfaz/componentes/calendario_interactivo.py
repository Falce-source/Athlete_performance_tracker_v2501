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
    - eventos: lista de diccionarios con al menos 'start' (YYYY-MM-DD) y 'allDay'.
    - id_atleta: necesario para registrar nuevos estados diarios.
    """
    # ───────────────────────────────
    # Inicialización robusta
    # ───────────────────────────────
    # Normalizamos la entrada a lista en una variable local
    eventos = eventos if isinstance(eventos, list) else []

    st.markdown("### 🗓️ Calendario interactivo")

    # Construcción de eventos agrupados por día
    fc_events = []
    for ev in eventos:
        fecha = ev.get("start")
        if not fecha:
            continue

        tipo = ev.get("Tipo") or ev.get("tipo_evento")
        details = ev.get("extendedProps", {})

        if tipo == "estado_diario":
            ciclo_icons, entreno_icons, resto_icons = [], [], []
            if details.get("Síntomas"): ciclo_icons.append(EVENT_STYLES["sintomas"]["icon"])
            if details.get("Menstruacion"): ciclo_icons.append(EVENT_STYLES["menstruacion"]["icon"])
            if details.get("Ovulacion"): ciclo_icons.append(EVENT_STYLES["ovulacion"]["icon"])
            if details.get("Altitud"): entreno_icons.append(EVENT_STYLES["altitud"]["icon"])
            if details.get("Respiratorio"): entreno_icons.append(EVENT_STYLES["respiratorio"]["icon"])
            if details.get("Calor"): entreno_icons.append(EVENT_STYLES["calor"]["icon"])
            if details.get("Lesión"): resto_icons.append(EVENT_STYLES["lesion"]["icon"])
            if details.get("Comentario"): resto_icons.append(EVENT_STYLES["nota"]["icon"])

            fc_events.append({
                "id": str(ev.get("id")),
                "title": "🧍 Estado diario",
                "start": fecha,
                "allDay": True,
                "backgroundColor": EVENT_STYLES["estado"]["bg"],
                "borderColor": EVENT_STYLES["estado"]["border"],
                "textColor": EVENT_STYLES["estado"]["text"],
                "extendedProps": {**details, "displayOrder": 0}
            })
            if ciclo_icons:
                fc_events.append({"title": " ".join(ciclo_icons), "start": fecha, "allDay": True,
                                  "backgroundColor": "transparent", "borderColor": "transparent",
                                  "textColor": EVENT_STYLES["estado"]["text"],
                                  "extendedProps": {**details, "displayOrder": 1}})
            if entreno_icons:
                fc_events.append({"title": " ".join(entreno_icons), "start": fecha, "allDay": True,
                                  "backgroundColor": "transparent", "borderColor": "transparent",
                                  "textColor": EVENT_STYLES["estado"]["text"],
                                  "extendedProps": {**details, "displayOrder": 2}})
            if resto_icons:
                fc_events.append({"title": " ".join(resto_icons), "start": fecha, "allDay": True,
                                  "backgroundColor": "transparent", "borderColor": "transparent",
                                  "textColor": EVENT_STYLES["estado"]["text"],
                                  "extendedProps": {**details, "displayOrder": 3}})

        elif tipo == "competicion":
            fc_events.append({
                "id": str(ev.get("id")),
                "title": "🏆 Competición",
                "start": fecha,
                "allDay": True,
                "backgroundColor": "#FFF4E5",
                "borderColor": "#F97316",
                "textColor": "#7C2D12",
                "extendedProps": {**details, "displayOrder": 0}
            })

        elif tipo == "cita_test":
            fc_events.append({
                "id": str(ev.get("id")),
                "title": "📅 Cita/Test",
                "start": fecha,
                "allDay": True,
                "backgroundColor": EVENT_STYLES["cita_test"]["bg"],
                "borderColor": EVENT_STYLES["cita_test"]["border"],
                "textColor": EVENT_STYLES["cita_test"]["text"],
                "extendedProps": {**details, "displayOrder": 0}
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
        "eventOrder": "displayOrder",
        "timeZone": "UTC",            # interpreta YYYY-MM-DD sin desfase
        "forceEventDuration": True,
        "displayEventEnd": False
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

    # Modal de registro al hacer clic en un día vacío
    if "dateClick" in st.session_state:
        fecha_iso = st.session_state["dateClick"].get("dateStr") or st.session_state["dateClick"].get("date")
        if isinstance(fecha_iso, str):
            if "T" in fecha_iso:
                fecha_iso = fecha_iso.split("T")[0]
            fecha_local = datetime.date.fromisoformat(fecha_iso)
        elif isinstance(fecha_iso, datetime.date):
            fecha_local = fecha_iso
        else:
            fecha_local = datetime.date.today()

        @st.dialog(f"➕ Registrar evento para {fecha_local.strftime('%Y-%m-%d')}")
        def registrar_evento():
            tipo_evento = st.radio(
                "Selecciona el tipo de evento",
                ["Estado diario", "Competición", "Cita/Test"]
            )

            if tipo_evento == "Estado diario":
                with st.form("form_estado_diario", clear_on_submit=True):
                    with st.expander("🩸 Datos de ciclo"):
                        sintomas = st.selectbox("Síntomas", ["Ninguno","Dolor leve","Dolor moderado","Dolor intenso"])
                        menstruacion = st.selectbox("Menstruación", ["No","Día 1","Día 2","Día 3","Día 4+"])
                        ovulacion = st.selectbox("Ovulación", ["No","Estimada","Confirmada"])
                    altitud = st.checkbox("⛰️ Entrenamiento en altitud")
                    respiratorio = st.checkbox("🌬️ Entrenamiento respiratorio")
                    calor = st.checkbox("🔥 Entrenamiento en calor")
                    lesion = st.text_input("🤕 Lesión")
                    comentario_extra = st.text_area("📝 Notas adicionales")
                    if st.form_submit_button("Guardar estado"):
                        sql.crear_evento_calendario(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),  # normalizamos a string
                            tipo_evento="estado_diario",
                            valor={
                                "Síntomas": sintomas,
                                "Menstruacion": menstruacion,
                                "Ovulacion": ovulacion,
                                "Altitud": altitud,
                                "Respiratorio": respiratorio,
                                "Calor": calor,
                                "Lesión": lesion,
                                "Comentario": comentario_extra
                            },
                            notas=None
                        )
                        st.success("✅ Estado diario registrado")
                        st.rerun()

            elif tipo_evento == "Competición":
                with st.form("form_competicion", clear_on_submit=True):
                    nombre = st.text_input("Nombre de la competición")
                    lugar = st.text_input("Lugar")
                    notas = st.text_area("Notas")
                    if st.form_submit_button("Guardar competición"):
                        sql.crear_competicion(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),
                            detalles={"nombre": nombre, "lugar": lugar},
                            notas=notas
                        )
                        st.success("✅ Competición registrada")
                        st.rerun()

            elif tipo_evento == "Cita/Test":
                with st.form("form_cita_test", clear_on_submit=True):
                    tipo = st.text_input("Tipo de cita/test")
                    lugar = st.text_input("Lugar")
                    notas = st.text_area("Notas")
                    if st.form_submit_button("Guardar cita/test"):
                        sql.crear_cita_test(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),
                            detalles={"tipo": tipo, "lugar": lugar},
                            notas=notas
                        )
                        st.success("✅ Cita/Test registrada")
                        st.rerun()

        registrar_evento()

    # Renderizar calendario (ahora \n se interpreta como salto de línea)
    cal = calendar(events=fc_events, options=calendar_options)

    # Modal editable al hacer clic en la cabecera
    if cal and "eventClick" in cal:
        ev = cal["eventClick"]["event"]
        props = ev.get("extendedProps", {})
        if props and props.get("displayOrder") == 0 and ev.get("title") == "🧍 Estado diario":
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

                    lesion = st.text_input("🤕 Lesión", value=props.get("Lesión",""))
                    comentario_extra = st.text_area("📝 Notas adicionales", value=props.get("Comentario",""))

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar cambios")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        event_id = ev.get("id")
                        if event_id:
                            sql.actualizar_evento_calendario_por_id(
                                id_evento=int(event_id),
                                valores_actualizados={
                                    "Sintomas": sintomas,
                                    "Menstruacion": menstruacion,
                                    "Ovulacion": ovulacion,
                                    "Altitud": altitud,
                                    "Respiratorio": respiratorio,
                                    "Calor": calor,
                                    "Lesion": lesion,
                                    "Comentario_extra": comentario_extra
                                }
                            )
                            st.success("✅ Estado diario actualizado")
                        else:
                            st.error("❌ No se pudo identificar el evento")
                        st.rerun()  # recarga para cerrar modal y refrescar calendario

                    if eliminar:
                        event_id = ev.get("id")
                        if event_id and sql.borrar_evento_calendario(int(event_id)):
                            st.success("🗑️ Estado diario eliminado")
                        else:
                            st.error("❌ No se pudo eliminar el evento")
                        st.rerun()  # recarga para cerrar modal y refrescar calendario

            editar_estado()
    
        # Modal para editar competición
        if ev.get("title") == "🏆 Competición":
            @st.dialog("🏆 Editar competición")
            def editar_competicion():
                with st.form("form_editar_competicion", clear_on_submit=True):
                    detalles = props or {}
                    nombre = st.text_input("Nombre", value=detalles.get("nombre",""))
                    lugar = st.text_input("Lugar", value=detalles.get("lugar",""))
                    notas = st.text_area("Notas", value=detalles.get("notas",""))

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        sql.actualizar_evento_calendario_por_id(
                            id_evento=int(ev.get("id")),
                            valores_actualizados={"nombre": nombre, "lugar": lugar},
                            notas=notas
                        )
                        st.success("✅ Competición actualizada")
                        st.rerun()
                    if eliminar:
                        sql.borrar_evento_calendario(int(ev.get("id")))
                        st.success("🗑️ Competición eliminada")
                        st.rerun()
            editar_competicion()

        # Modal para editar cita/test
        if ev.get("title") == "📅 Cita/Test":
            @st.dialog("📅 Editar cita/test")
            def editar_cita_test():
                with st.form("form_editar_cita_test", clear_on_submit=True):
                    detalles = props or {}
                    tipo = st.text_input("Tipo", value=detalles.get("tipo",""))
                    lugar = st.text_input("Lugar", value=detalles.get("lugar",""))
                    notas = st.text_area("Notas", value=detalles.get("notas",""))

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        sql.actualizar_evento_calendario_por_id(
                            id_evento=int(ev.get("id")),
                            valores_actualizados={"tipo": tipo, "lugar": lugar},
                            notas=notas
                        )
                        st.success("✅ Cita/Test actualizada")
                        st.rerun()
                    if eliminar:
                        sql.borrar_evento_calendario(int(ev.get("id")))
                        st.success("🗑️ Cita/Test eliminada")
                        st.rerun()
            editar_cita_test()
