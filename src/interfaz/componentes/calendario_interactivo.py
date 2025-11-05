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

def mostrar_calendario_interactivo(fc_events, id_atleta, vista="Calendario"):
    """
    Renderiza un calendario interactivo tipo TrainingPeaks usando streamlit-calendar.
    - eventos: lista de diccionarios con al menos 'start' (YYYY-MM-DD) y 'allDay'.
    - id_atleta: necesario para registrar nuevos estados diarios.
    """
    import json

    # Helper interno para normalizar extendedProps
    def normalize_details(details: dict) -> dict:
        safe = {}
        for k, v in (details or {}).items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                safe[k] = v
            elif isinstance(v, (datetime.date, datetime.datetime)):
                safe[k] = v.isoformat()
            else:
                safe[k] = str(v)
        return safe

    # ───────────────────────────────
    # Inicialización robusta
    # ───────────────────────────────
    # Normalizamos la lista de eventos
    src_events = fc_events if isinstance(fc_events, list) else []
    out_events = []

    st.markdown("### 🗓️ Calendario interactivo")

    # Construcción de eventos agrupados por día
    for ev in src_events:
        fecha = ev.get("start")
        if not fecha:
            continue

        tipo = ev.get("Tipo") or ev.get("tipo_evento")
        details = ev.get("extendedProps", {})

        if tipo == "estado_diario":
            # Agrupamos iconos por filas
            fila2, fila3 = [], []
            if details.get("sintomas") not in [None, "", "No", "Ninguno", "-"]:
                fila2.append(EVENT_STYLES["sintomas"]["icon"])
            if details.get("menstruacion") not in [None, "", "No", "-"]:
                fila2.append(EVENT_STYLES["menstruacion"]["icon"])
            if details.get("ovulacion") not in [None, "", "No", "-"]:
                fila2.append(EVENT_STYLES["ovulacion"]["icon"])
            if details.get("lesion"): fila2.append(EVENT_STYLES["lesion"]["icon"])
            if details.get("comentario_extra"): fila2.append(EVENT_STYLES["nota"]["icon"])

            if details.get("altitud"): fila3.append(EVENT_STYLES["altitud"]["icon"])
            if details.get("respiratorio"): fila3.append(EVENT_STYLES["respiratorio"]["icon"])
            if details.get("calor"): fila3.append(EVENT_STYLES["calor"]["icon"])

            safe_details = normalize_details(details)

            # 🔑 ExtendedProps común con id_base
            extended = {**safe_details, "tipo_evento": tipo, "id_base": ev.get("id")}

            # Fila 1: título principal (verde)
            # Solo creamos el título verde si hay algún dato realmente relevante
            datos_relevantes = any(
                v not in [None, "", "No", "Ninguno", "-"]
                for k, v in details.items()
                if k in ["sintomas", "menstruacion", "ovulacion", "altitud",
                         "respiratorio", "calor", "lesion", "comentario_extra"]
            )
            if datos_relevantes:
                out_events.append({
                    "id": f"{ev.get('id')}-0",
                    "title": "🧍 Evento diario",
                    "start": fecha,
                    "allDay": True,
                    "backgroundColor": EVENT_STYLES["estado"]["bg"],
                    "borderColor": EVENT_STYLES["estado"]["border"],
                    "textColor": EVENT_STYLES["estado"]["text"],
                    "tipo_evento": tipo,
                    "extendedProps": {**extended, "displayOrder": 0}
                })

            # Fila 2: ciclo/estado corporal (neutro)
            if fila2:
                out_events.append({
                    "id": f"{ev.get('id')}-1",
                    "title": " ".join(fila2),
                    "start": fecha,
                    "allDay": True,
                    "backgroundColor": "#FFFFFF",   # fondo blanco
                    "borderColor": "#FFFFFF",       # sin borde
                    "textColor": "#000000",         # texto negro
                    "tipo_evento": tipo,
                    "extendedProps": {**extended, "displayOrder": 1}
                })

            # Fila 3: condiciones externas (neutro)
            if fila3:
                out_events.append({
                    "id": f"{ev.get('id')}-2",
                    "title": " ".join(fila3),
                    "start": fecha,
                    "allDay": True,
                    "backgroundColor": "#FFFFFF",   # fondo blanco
                    "borderColor": "#FFFFFF",       # sin borde
                    "textColor": "#000000",         # texto negro
                    "tipo_evento": tipo,
                    "extendedProps": {**extended, "displayOrder": 2}
                })

        elif tipo == "competicion":
            # Solo icono 🏆, detalles en extendedProps
            safe_details = normalize_details(details)
            out_events.append({
                "id": str(ev.get("id")),
                "title": "🏆",
                "start": fecha,
                "allDay": True,
                "backgroundColor": "#FFF4E5",
                "borderColor": "#F97316",
                "textColor": "#7C2D12",
                "tipo_evento": tipo,
                "extendedProps": {**safe_details, "displayOrder": 3, "tipo_evento": tipo, "id_base": ev.get("id")}
            })

        elif tipo == "cita_test":
            # Solo icono 📅, detalles en extendedProps
            safe_details = normalize_details(details)
            out_events.append({
                "id": str(ev.get("id")),
                "title": "📅",
                "start": fecha,
                "allDay": True,
                "backgroundColor": EVENT_STYLES["cita_test"]["bg"],
                "borderColor": EVENT_STYLES["cita_test"]["border"],
                "textColor": EVENT_STYLES["cita_test"]["text"],
                "tipo_evento": tipo,
                "extendedProps": {**safe_details, "displayOrder": 3, "tipo_evento": tipo, "id_base": ev.get("id")}
            })

    # Configuración del calendario (sin eventContent, usamos saltos de línea en title)
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
        "timeZone": "UTC",
        "forceEventDuration": True,
        "displayEventEnd": False
    }

    # Renderizar calendario (ahora \n se interpreta como salto de línea)
    # Renderizar calendario (una sola vez)
    # 🔑 Usamos un key único combinando id_atleta y vista

    cal = calendar(
        events=out_events,
        options=calendar_options,
        key=f"calendar_{id_atleta}_{vista}"
    )

    # Modal de registro al hacer clic en un día vacío
    if cal and "dateClick" in cal:
        fecha_iso = cal["dateClick"].get("dateStr") or cal["dateClick"].get("date")
        if isinstance(fecha_iso, str):
            if "T" in fecha_iso:
                fecha_iso = fecha_iso.split("T")[0]
            fecha_local = datetime.date.fromisoformat(fecha_iso)
        elif isinstance(fecha_iso, datetime.date):
            fecha_local = fecha_iso
        else:
            fecha_local = datetime.date.today()

        # Verificamos si ya hay un estado_diario en esa fecha
        ya_existe = any(
            ev.get("tipo_evento") == "estado_diario"
            and ev.get("start", "").startswith(str(fecha_local))
            for ev in src_events
        )

        @st.dialog(f"➕ Registrar evento para {fecha_local.strftime('%Y-%m-%d')}")
        def registrar_evento():
            opciones = ["Competición", "Cita/Test"]
            if not ya_existe:
                opciones.insert(0, "Estado diario")
            tipo_evento = st.radio("Selecciona el tipo de evento", opciones)

            # -------------------------
            # Estado diario
            # -------------------------
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
                        valores = normalize_details({
                            "sintomas": sintomas,
                            "menstruacion": menstruacion,
                            "ovulacion": ovulacion,
                            "altitud": altitud,
                            "respiratorio": respiratorio,
                            "calor": calor,
                            "lesion": lesion,
                            "comentario_extra": comentario_extra
                        })
                        sql.crear_evento_calendario(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),
                            tipo_evento="estado_diario",
                            valor=valores,
                            notas=None
                        )
                        st.success("✅ Estado diario registrado")
                        st.rerun()

            # -------------------------
            # Competición
            # -------------------------
            elif tipo_evento == "Competición":
                with st.form("form_competicion", clear_on_submit=True):
                    nombre = st.text_input("Nombre")
                    lugar = st.text_input("Lugar")
                    notas = st.text_area("Notas")

                    if st.form_submit_button("Guardar competición"):
                        valores = normalize_details({"nombre": nombre, "lugar": lugar})
                        sql.crear_evento_calendario(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),
                            tipo_evento="competicion",
                            valor=valores,
                            notas=notas
                        )
                        st.success("✅ Competición registrada")
                        st.rerun()

            # -------------------------
            # Cita/Test
            # -------------------------
            elif tipo_evento == "Cita/Test":
                with st.form("form_cita_test", clear_on_submit=True):
                    tipo = st.text_input("Tipo")
                    lugar = st.text_input("Lugar")
                    notas = st.text_area("Notas")

                    if st.form_submit_button("Guardar cita/test"):
                        valores = normalize_details({"tipo": tipo, "lugar": lugar})
                        sql.crear_evento_calendario(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),
                            tipo_evento="cita_test",
                            valor=valores,
                            notas=notas
                        )
                        st.success("✅ Cita/Test registrada")
                        st.rerun()

        registrar_evento()
    
    # Modal editable al hacer clic en un evento
    if cal and "eventClick" in cal:
        ev = cal["eventClick"]["event"]
        props = ev.get("extendedProps", {}) or {}
        tipo_ev = props.get("tipo_evento") or ev.get("tipo_evento")

        # -------------------------
        # Estado diario
        # -------------------------
        if tipo_ev == "estado_diario":
            @st.dialog("📋 Editar estado diario")
            def editar_estado():
                with st.form("form_editar_estado", clear_on_submit=True):
                    sintomas = st.selectbox(
                        "Síntomas menstruales",
                        ["Ninguno","Dolor leve","Dolor moderado","Dolor intenso"],
                        index=["Ninguno","Dolor leve","Dolor moderado","Dolor intenso"].index(props.get("sintomas","Ninguno"))
                    )
                    menstruacion = st.selectbox(
                        "Menstruación",
                        ["No","Día 1","Día 2","Día 3","Día 4+"],
                        index=["No","Día 1","Día 2","Día 3","Día 4+"].index(props.get("menstruacion","No"))
                    )
                    ovulacion = st.selectbox(
                        "Ovulación",
                        ["No","Estimada","Confirmada"],
                        index=["No","Estimada","Confirmada"].index(props.get("ovulacion","No"))
                    )

                    altitud = st.checkbox("⛰️ Entrenamiento en altitud", value=bool(props.get("altitud")))
                    respiratorio = st.checkbox("🌬️ Entrenamiento respiratorio", value=bool(props.get("respiratorio")))
                    calor = st.checkbox("🔥 Entrenamiento en calor", value=bool(props.get("calor")))

                    lesion = st.text_input("🤕 Lesión", value=props.get("lesion",""))
                    comentario_extra = st.text_area("📝 Notas adicionales", value=props.get("comentario_extra",""))

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar cambios")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        event_id = props.get("id_base")
                        if event_id is not None:
                            valores = normalize_details({
                                "sintomas": sintomas,
                                "menstruacion": menstruacion,
                                "ovulacion": ovulacion,
                                "altitud": altitud,
                                "respiratorio": respiratorio,
                                "calor": calor,
                                "lesion": lesion,
                                "comentario_extra": comentario_extra
                            })
                            sql.actualizar_evento_calendario_por_id(
                                id_evento=int(event_id),
                                valores_actualizados=valores
                            )
                            st.success("✅ Estado diario actualizado")

                        else:
                            st.error("❌ No se pudo identificar el evento")
                        st.rerun()

                    if eliminar:
                        event_id = props.get("id_base")
                        if event_id is not None and sql.borrar_evento_calendario(int(event_id)):
                            st.success("🗑️ Estado diario eliminado")
                        else:
                            st.error("❌ No se pudo eliminar el evento")
                        st.rerun()
            editar_estado()

        # -------------------------
        # Competición
        # -------------------------
        if tipo_ev == "competicion":
            @st.dialog("🏆 Editar competición")
            def editar_competicion():
                with st.form("form_editar_competicion", clear_on_submit=True):
                    nombre = st.text_input("Nombre", value=props.get("nombre",""))
                    lugar = st.text_input("Lugar", value=props.get("lugar",""))
                    notas = st.text_area("Notas", value=props.get("notas",""))

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        event_id = props.get("id_base") or ev.get("id")
                        if event_id:
                            valores = normalize_details({
                                "nombre": nombre,
                                "lugar": lugar
                            })
                            sql.actualizar_evento_calendario_por_id(
                                id_evento=int(event_id),
                                valores_actualizados=valores,
                                notas=notas
                            )
                            st.success("✅ Competición actualizada")
                        st.rerun()
                    if eliminar:
                        event_id = props.get("id_base") or ev.get("id")
                        if event_id:
                            sql.borrar_evento_calendario(int(event_id))
                            st.success("🗑️ Competición eliminada")
                        st.rerun()
            editar_competicion()

        # -------------------------
        # Cita/Test
        # -------------------------
        if tipo_ev == "cita_test":
            @st.dialog("📅 Editar cita/test")
            def editar_cita_test():
                with st.form("form_editar_cita_test", clear_on_submit=True):
                    tipo = st.text_input("Tipo", value=props.get("tipo",""))
                    lugar = st.text_input("Lugar", value=props.get("lugar",""))
                    notas = st.text_area("Notas", value=props.get("notas",""))

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        event_id = props.get("id_base") or ev.get("id")
                        if event_id:
                            valores = normalize_details({
                                "tipo": tipo,
                                "lugar": lugar
                            })
                            sql.actualizar_evento_calendario_por_id(
                                id_evento=int(event_id),
                                valores_actualizados=valores,
                                notas=notas
                            )
                            st.success("✅ Cita/Test actualizada")
                        st.rerun()
                    if eliminar:
                        event_id = props.get("id_base") or ev.get("id")
                        if event_id:
                            sql.borrar_evento_calendario(int(event_id))
                            st.success("🗑️ Cita/Test eliminada")
                        st.rerun()
            editar_cita_test()