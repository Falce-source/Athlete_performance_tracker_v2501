import streamlit as st
from streamlit_calendar import calendar
import datetime
import src.persistencia.sql as sql

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
            safe_details = normalize_details(details)
            extended = {**safe_details, "tipo_evento": tipo, "id_base": ev.get("id")}

            valores_neutros = [None, "", "No", "Ninguno", "-", False]

            # Bloque 1: ciclo
            fila_ciclo = []
            if details.get("sintomas") not in valores_neutros: fila_ciclo.append("🩸")
            if details.get("menstruacion") not in valores_neutros: fila_ciclo.append("🩸")
            if details.get("ovulacion") not in valores_neutros: fila_ciclo.append("🔄")
            if fila_ciclo:
                out_events.append({"id": f"{ev.get('id')}-ciclo", "title": " ".join(fila_ciclo),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 0}})

            # Bloque 2: condiciones externas
            fila_cond = []
            if details.get("altitud"): fila_cond.append("⛰️")
            if details.get("calor"): fila_cond.append("🔥")
            if details.get("respiratorio"): fila_cond.append("🌬️")
            if fila_cond:
                out_events.append({"id": f"{ev.get('id')}-cond", "title": " ".join(fila_cond),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 1}})

            # Bloque 3: lesiones / baja / notas
            fila_extra = []
            if details.get("lesion"): fila_extra.append("🤕")
            if details.get("baja") and details.get("baja") != "No":
                fila_extra.append("⛔")
            if details.get("comentario_extra"): fila_extra.append("📝")
            if fila_extra:
                out_events.append({"id": f"{ev.get('id')}-extra", "title": " ".join(fila_extra),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 2}})

            # Bloque 4: peso/déficit
            fila_peso = []
            if details.get("peso"): fila_peso.append(f"⚖️ {details['peso']}")
            if details.get("deficit_calorico"): fila_peso.append("🍽️")
            if fila_peso:
                out_events.append({"id": f"{ev.get('id')}-peso", "title": " ".join(fila_peso),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 3}})

            # Bloque 5: HRV / FC reposo
            fila_hrv = []
            if details.get("hrv"): fila_hrv.append(f"💓 {details['hrv']}")
            if details.get("fc_reposo"): fila_hrv.append(f"❤️ {details['fc_reposo']}")
            if fila_hrv:
                out_events.append({"id": f"{ev.get('id')}-hrv", "title": " ".join(fila_hrv),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 4}})

            # Bloque 6: sueño / wellness / RPE
            fila_sueno = []
            if details.get("sueno"): fila_sueno.append(f"😴 {details['sueno']}h")
            if details.get("wellness"): fila_sueno.append(f"🌟 {details['wellness']}")
            if details.get("rpe"): fila_sueno.append(f"💪 {details['rpe']}")
            if fila_sueno:
                out_events.append({"id": f"{ev.get('id')}-sueno", "title": " ".join(fila_sueno),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 5}})

        elif tipo == "competicion":
            # Solo icono 🏆, detalles en extendedProps
            safe_details = normalize_details(details)
            out_events.append({
                "id": str(ev.get("id")),
                "title": "🏆",
                "start": fecha,
                "allDay": True,
                "backgroundColor": "#FFFFFF",
                "borderColor": "#FFFFFF",
                "textColor": "#000000",
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
            safe_details = normalize_details(details)
            extended = {**safe_details, "tipo_evento": tipo, "id_base": ev.get("id")}

            # Bloque A: peso / déficit
            fila_peso = []
            if safe_details.get("peso"): fila_peso.append(f"⚖️ {safe_details['peso']}kg")
            if safe_details.get("deficit_calorico"):
                fila_peso.append(f"🍽️ {safe_details['deficit_calorico']}")
            if fila_peso:
                out_events.append({"id": f"{ev.get('id')}-peso", "title": " ".join(fila_peso),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 3}})

            # Bloque B: HRV / FC reposo
            fila_hrv = []
            if safe_details.get("hrv"): fila_hrv.append(f"💓 {safe_details['hrv']}")
            if safe_details.get("fc_reposo"): fila_hrv.append(f"❤️ {safe_details['fc_reposo']}")
            if fila_hrv:
                out_events.append({"id": f"{ev.get('id')}-hrv", "title": " ".join(fila_hrv),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 4}})

            # Bloque C: sueño / wellness / RPE
            fila_sueno = []
            if safe_details.get("sueno"): fila_sueno.append(f"😴 {safe_details['sueno']}h")
            if safe_details.get("wellness"): fila_sueno.append(f"🌟 {safe_details['wellness']}")
            if safe_details.get("rpe"): fila_sueno.append(f"💪 {safe_details['rpe']}")
            if fila_sueno:
                out_events.append({"id": f"{ev.get('id')}-sueno", "title": " ".join(fila_sueno),
                    "start": fecha, "allDay": True, "backgroundColor": "#FFFFFF",
                    "borderColor": "#FFFFFF", "textColor": "#000000",
                    "tipo_evento": tipo, "extendedProps": {**extended, "displayOrder": 5}})

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
        ya_existe_estado = any(
            ev.get("tipo_evento") == "estado_diario"
            and ev.get("start", "").startswith(str(fecha_local))
            for ev in src_events
        )

        # Verificamos si ya hay métricas rápidas en esa fecha
        ya_existe_metricas = any(
            ev.get("tipo_evento") == "metricas_rapidas"
            and ev.get("start", "").startswith(str(fecha_local))
            for ev in src_events
        )

        @st.dialog(f"➕ Registrar evento para {fecha_local.strftime('%Y-%m-%d')}")
        def registrar_evento():
            opciones = ["Competición", "Cita/Test"]
            if not ya_existe_estado:
                opciones.insert(0, "Estado diario")
            if not ya_existe_metricas:
                opciones.append("Métricas rápidas")
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
                    baja = st.selectbox("⛔ Baja", ["No", "No entrena", "No compite"])
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
                            "baja": baja,
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
                        # Guardamos en tabla métricas (histórico) con la fecha del evento
                        if hrv != 0: 
                            sql.crear_metrica(id_atleta, "hrv", hrv, "ms", fecha=fecha_local)
                        if wellness != 0:
                            sql.crear_metrica(id_atleta, "wellness", wellness, "score", fecha=fecha_local)
                        if rpe != 0:
                            sql.crear_metrica(id_atleta, "rpe", rpe, "score", fecha=fecha_local)
                        if peso != 0.0:
                            sql.crear_metrica(id_atleta, "peso", peso, "kg", fecha=fecha_local)
                        if fc_reposo != 0:
                            sql.crear_metrica(id_atleta, "fc_reposo", fc_reposo, "lpm", fecha=fecha_local)

                        # Creamos también un evento de calendario para que aparezca en la cuadrícula
                        sql.crear_evento_calendario(
                            id_atleta=id_atleta,
                            fecha=str(fecha_local),
                            tipo_evento="metricas_rapidas",
                            valor={k: v for k, v in {
                                "hrv": hrv,
                                "wellness": wellness,
                                "rpe": rpe,
                                "peso": peso,
                                "fc_reposo": fc_reposo
                            }.items() if v != 0},
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
                    baja = st.selectbox(
                        "⛔ Baja",
                        ["No","No entrena","No compite"],
                        index=["No","No entrena","No compite"].index(props.get("baja","No"))
                    )
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
                                "baja": baja,
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
                    col1, col2 = st.columns(2)
                    with col1:
                        peso = st.number_input("⚖️ Peso (kg)", min_value=0.0, step=0.1,
                            value=float(props.get("peso", 0)) if props.get("peso") else 0.0)
                        deficit_calorico = st.text_input("🍽️ Déficit calórico", value=props.get("deficit_calorico",""))
                        hrv = st.number_input("💓 HRV (ms)", min_value=0, step=1,
                            value=int(props.get("hrv", 0)) if props.get("hrv") else 0)
                    with col2:
                        fc_reposo = st.number_input("❤️ FC reposo (lpm)", min_value=0, step=1,
                            value=int(props.get("fc_reposo", 0)) if props.get("fc_reposo") else 0)
                        sueno = st.number_input("😴 Horas de sueño", min_value=0.0, step=0.5,
                            value=float(props.get("sueno", 0)) if props.get("sueno") else 0.0)
                        wellness = st.slider("🌟 Wellness (1-10)", 1, 10,
                            int(props.get("wellness", 5)) if props.get("wellness") else 5)
                        rpe = st.slider("💪 RPE (1-10)", 1, 10,
                            int(props.get("rpe", 5)) if props.get("rpe") else 5)

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Guardar")
                    with col2:
                        eliminar = st.form_submit_button("🗑️ Eliminar")

                    if submitted:
                        # Guardamos en histórico (tabla métricas) con la fecha del evento
                        fecha_evento = ev.get("start") or fecha_local
                        if peso != 0.0:
                            sql.crear_metrica(id_atleta, "peso", peso, "kg", fecha=fecha_evento)
                        if deficit_calorico:
                            sql.crear_metrica(id_atleta, "deficit_calorico", deficit_calorico, "kcal", fecha=fecha_evento)
                        if hrv != 0:
                            sql.crear_metrica(id_atleta, "hrv", hrv, "ms", fecha=fecha_evento)
                        if fc_reposo != 0:
                            sql.crear_metrica(id_atleta, "fc_reposo", fc_reposo, "lpm", fecha=fecha_evento)
                        if sueno != 0.0:
                            sql.crear_metrica(id_atleta, "sueno", sueno, "h", fecha=fecha_evento)
                        if wellness != 0:
                            sql.crear_metrica(id_atleta, "wellness", wellness, "score", fecha=fecha_evento)
                        if rpe != 0:
                            sql.crear_metrica(id_atleta, "rpe", rpe, "score", fecha=fecha_evento)

                        # Actualizamos el evento existente en calendario_eventos
                        event_id = props.get("id_base") or ev.get("id")
                        if event_id:
                           sql.actualizar_evento_calendario_por_id(
                                int(event_id),
                                {
                                    "peso": peso,
                                    "deficit_calorico": deficit_calorico,
                                    "hrv": hrv,
                                    "fc_reposo": fc_reposo,
                                    "sueno": sueno,
                                    "wellness": wellness,
                                    "rpe": rpe
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
                                eliminado = sql.borrar_evento_calendario(int(event_id))
                                # 🔒 Además borramos métricas rápidas asociadas en BD
                                fecha_evento = ev.get("start") or fecha_local
                                borradas = sql.borrar_metricas_por_fecha(id_atleta, fecha_evento)
                                if eliminado or borradas > 0:
                                    st.success("🗑️ Métricas rápidas eliminadas")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Este evento de métricas rápidas ya no existe (posiblemente fue borrado).")
                            else:
                                st.caption("⛔ No tienes permisos para borrar estas métricas rápidas")
            editar_metricas_rapidas()
