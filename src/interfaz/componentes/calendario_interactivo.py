import streamlit as st
from streamlit_calendar import calendar
import datetime
from src.persistencia import sql

# Importar control de roles
from src.utils.roles import Contexto, puede_borrar_evento_calendario

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

    # 🔑 Nota: ahora fc_events puede venir ya filtrado desde calendario.py
    # No requiere cambios internos, solo aseguramos compatibilidad.

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
            claves_relevantes = [
                "sintomas", "menstruacion", "ovulacion",
                "altitud", "respiratorio", "calor",
                "lesion", "comentario_extra"
            ]
            valores_neutros = [None, "", "No", "Ninguno", "-", False]
            datos_relevantes = any(
                details.get(k) not in valores_neutros
                for k in claves_relevantes
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

        elif tipo == "metricas_rapidas":
            # Mostrar iconos + valores numéricos en la casilla
            safe_details = normalize_details(details)
            fila_metricas = []
            if safe_details.get("hrv"): fila_metricas.append(f"💓 {safe_details['hrv']}")
            if safe_details.get("wellness"): fila_metricas.append(f"🌟 {safe_details['wellness']}")
            if safe_details.get("rpe"): fila_metricas.append(f"💪 {safe_details['rpe']}")
            if safe_details.get("peso"): fila_metricas.append(f"⚖️ {safe_details['peso']}")
            if safe_details.get("fc_reposo"): fila_metricas.append(f"❤️ {safe_details['fc_reposo']}")

            if fila_metricas:
                out_events.append({
                    "id": str(ev.get("id")),
                    "title": " ".join(fila_metricas),
                    "start": fecha,
                    "allDay": True,
                    "backgroundColor": "#F9FAFB",
                    "borderColor": "#6B7280",
                    "textColor": "#374151",
                    "tipo_evento": tipo,
                    "extendedProps": {**safe_details, "displayOrder": 4, "tipo_evento": tipo, "id_base": ev.get("id")}
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
            opciones = ["Competición", "Cita/Test", "Métricas rápidas"]
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
                        # Detectar si hay algún dato realmente significativo
                        valores_neutros = [None, "", "No", "Ninguno", "-", False]
                        datos_relevantes = any(v not in valores_neutros for v in valores.values())

                        if datos_relevantes:
                            sql.crear_evento_calendario(
                                id_atleta=id_atleta,
                                fecha=str(fecha_local),
                                tipo_evento="estado_diario",
                                valor=valores,
                                notas=None
                            )
                            st.success("✅ Estado diario registrado")
                            st.rerun()
                        else:
                            st.info("ℹ️ No se guardó el evento porque no contiene datos")

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
    
            # -------------------------
            # Métricas rápidas
            # -------------------------
            elif tipo_evento == "Métricas rápidas":
                with st.form("form_metricas_rapidas", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        hrv = st.number_input("HRV (ms)", min_value=0, step=1)
                        wellness = st.slider("Wellness (1-10)", 1, 10, 5)
                        peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
                    with col2:
                        rpe = st.slider("RPE (1-10)", 1, 10, 5)
                        fc_reposo = st.number_input("FC reposo (lpm)", min_value=0, step=1)

                    if st.form_submit_button("Guardar métricas"):
                        # Guardamos en tabla métricas (histórico)
                        sql.crear_metrica(id_atleta, "hrv", hrv, "ms")
                        sql.crear_metrica(id_atleta, "wellness", wellness, "score")
                        sql.crear_metrica(id_atleta, "rpe", rpe, "score")
                        sql.crear_metrica(id_atleta, "peso", peso, "kg")
                        sql.crear_metrica(id_atleta, "fc_reposo", fc_reposo, "lpm")

                        # Creamos también un evento de calendario para que aparezca en la cuadrícula
                        sql.crear_evento_calendario(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),
                            tipo_evento="metricas_rapidas",
                            valor={
                                "hrv": hrv,
                                "wellness": wellness,
                                "rpe": rpe,
                                "peso": peso,
                                "fc_reposo": fc_reposo
                            },
                            notas="Métricas rápidas registradas"
                        )

                        st.success("✅ Métricas rápidas registradas")
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
                            valores_neutros = [None, "", "No", "Ninguno", "-", False]
                            datos_relevantes = any(v not in valores_neutros for v in valores.values())

                            if datos_relevantes:
                                sql.actualizar_evento_calendario_por_id(
                                    id_evento=int(event_id),
                                    valores_actualizados=valores
                                )
                                st.success("✅ Estado diario actualizado")
                            else:
                                # Si no hay datos relevantes, borramos el evento
                                sql.borrar_evento_calendario(int(event_id))
                                st.info("🗑️ Estado diario eliminado por quedar vacío")
                        else:
                            st.error("❌ No se pudo identificar el evento")
                        st.rerun()

                    # 🔑 Nuevo: borrado condicionado por rol
                    if eliminar:
                        event_id = props.get("id_base")
                        if event_id is not None:
                            ctx_evento = Contexto(
                                rol_actual=st.session_state.get("ROL_SIMULADO", st.session_state.get("ROL_ACTUAL", "admin")),
                                usuario_id=st.session_state.get("USUARIO_ID", 0),
                                atleta_id=id_atleta,
                                propietario_id=props.get("id_autor") or id_atleta
                            )
                            if ctx_evento.rol_actual == "admin" or puede_borrar_evento_calendario(ctx_evento):
                                sql.borrar_evento_calendario(int(event_id))
                                st.success(f"🗑️ Estado diario {event_id} eliminado")
                                st.rerun()
                            else:
                                st.caption("⛔ No tienes permisos para borrar este estado diario")
                        else:
                            st.error("❌ No se pudo identificar el evento para borrar")
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
                            ctx_evento = Contexto(
                                rol_actual=st.session_state.get("ROL_SIMULADO", st.session_state.get("ROL_ACTUAL", "admin")),
                                usuario_id=st.session_state.get("USUARIO_ID", 0),
                                atleta_id=id_atleta,
                                propietario_id=props.get("id_autor") or id_atleta
                            )
                            if ctx_evento.rol_actual == "admin" or puede_borrar_evento_calendario(ctx_evento):
                                sql.borrar_evento_calendario(int(event_id))
                                st.success("🗑️ Competición eliminada")
                                st.rerun()
                            else:
                                st.caption("⛔ No tienes permisos para borrar esta competición")
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
                            ctx_evento = Contexto(
                                rol_actual=st.session_state.get("ROL_SIMULADO", st.session_state.get("ROL_ACTUAL", "admin")),
                                usuario_id=st.session_state.get("USUARIO_ID", 0),
                                atleta_id=id_atleta,
                                propietario_id=props.get("id_autor") or id_atleta
                            )
                            if ctx_evento.rol_actual == "admin" or puede_borrar_evento_calendario(ctx_evento):
                                sql.borrar_evento_calendario(int(event_id))
                                st.success("🗑️ Cita/Test eliminada")
                                st.rerun()
                            else:
                                st.caption("⛔ No tienes permisos para borrar esta cita/test")
            editar_cita_test()

        # -------------------------
        # Métricas rápidas
        # -------------------------
        if tipo_ev == "metricas_rapidas":
            @st.dialog("📊 Editar métricas rápidas")
            def editar_metricas_rapidas():
                with st.form("form_editar_metricas_rapidas", clear_on_submit=True):
                    hrv = st.number_input("HRV (ms)", min_value=0, step=1,
                        value=int(props.get("hrv", 0)) if props.get("hrv") else 0)
                    wellness = st.slider("Wellness (1-10)", 1, 10,
                        int(props.get("wellness", 5)) if props.get("wellness") else 5)
                    rpe = st.slider("RPE (1-10)", 1, 10,
                        int(props.get("rpe", 5)) if props.get("rpe") else 5)
                    peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1,
                        value=float(props.get("peso", 0)) if props.get("peso") else 0.0)
                    fc_reposo = st.number_input("FC reposo (lpm)", min_value=0, step=1,
                        value=int(props.get("fc_reposo", 0)) if props.get("fc_reposo") else 0)

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        # Guardamos en histórico (tabla métricas)
                        sql.crear_metrica(id_atleta, "hrv", hrv, "ms")
                        sql.crear_metrica(id_atleta, "wellness", wellness, "score")
                        sql.crear_metrica(id_atleta, "rpe", rpe, "score")
                        sql.crear_metrica(id_atleta, "peso", peso, "kg")
                        sql.crear_metrica(id_atleta, "fc_reposo", fc_reposo, "lpm")

                        # Actualizamos el evento existente en calendario_eventos
                        event_id = props.get("id_base") or ev.get("id")
                        if event_id:
                            sql.actualizar_evento_calendario(
                                int(event_id),
                                tipo_evento="metricas_rapidas",
                                valor={
                                    "hrv": hrv,
                                    "wellness": wellness,
                                    "rpe": rpe,
                                    "peso": peso,
                                    "fc_reposo": fc_reposo
                                },
                                notas="Métricas rápidas actualizadas"
                            )
                        st.success("✅ Métricas rápidas actualizadas")
                        st.rerun()

                    if eliminar:
                        event_id = props.get("id_base") or ev.get("id")
                        if event_id:
                            ctx_evento = Contexto(
                                rol_actual=st.session_state.get("ROL_SIMULADO", st.session_state.get("ROL_ACTUAL", "admin")),
                                usuario_id=st.session_state.get("USUARIO_ID", 0),
                                atleta_id=id_atleta,
                                propietario_id=props.get("id_autor") or id_atleta
                            )
                            if ctx_evento.rol_actual == "admin" or puede_borrar_evento_calendario(ctx_evento):
                                sql.borrar_evento_calendario(int(event_id))
                                st.success("🗑️ Métricas rápidas eliminadas")
                                st.rerun()
                            else:
                                st.caption("⛔ No tienes permisos para borrar estas métricas rápidas")
            editar_metricas_rapidas()
