import streamlit as st
import pandas as pd
from datetime import datetime, UTC
from src.persistencia import sql
import json
from datetime import date

def badge(text, color="#eee", text_color="#000"):
    """Devuelve un span HTML con estilo tipo chip/badge."""
    return f"<span style='background-color:{color}; color:{text_color}; padding:2px 6px; border-radius:8px; font-size:90%'>{text}</span>"

def mostrar_calendario():
    st.header("📅 Calendario del atleta")

    # ───────────────────────────────
    # Selector de atleta
    # ───────────────────────────────
    atletas = sql.obtener_atletas()
    if not atletas:
        st.info("No hay atletas registrados todavía")
        return

    opciones = {f"{a.nombre} {a.apellidos or ''} (ID {a.id_atleta})": a.id_atleta for a in atletas}
    seleccion = st.selectbox("Selecciona un atleta", list(opciones.keys()))
    id_atleta = opciones[seleccion]

    st.markdown("---")

    # ───────────────────────────────
    # Formulario estados diarios (calendario_eventos)
    # ───────────────────────────────
    st.subheader("➕ Registrar estado diario")

    with st.form("form_estado_diario", clear_on_submit=True):
        fecha = st.date_input("Fecha", datetime.now(UTC).date())

        # Datos de ciclo (expander con varias opciones)
        with st.expander("🩸 Datos de ciclo"):
            sintomas = st.selectbox("Síntomas menstruales", ["Ninguno", "Dolor leve", "Dolor moderado", "Dolor intenso"])
            menstruacion = st.selectbox("Menstruación", ["No", "Día 1", "Día 2", "Día 3", "Día 4+"])
            ovulacion = st.selectbox("Ovulación", ["No", "Estimada", "Confirmada"])
        
        # Altitud, respiratorio y calor → todos como checkboxes simples
        altitud = st.checkbox("⛰️ Entrenamiento en altitud", key="altitud_checkbox")
        respiratorio = st.checkbox("🌬️ Entrenamiento respiratorio", key="respiratorio_checkbox")
        calor = st.checkbox("🔥 Entrenamiento en calor", key="calor_checkbox")

        # Citas/tests (expander con varias opciones)
        with st.expander("📅 Citas / Tests"):
            cita_test = st.selectbox("Selecciona", ["No", "Cita", "Test"], key="cita_test_select")

        # Competición → fecha + contador de días
        with st.expander("🏆 Competición"):
            fecha_competicion = st.date_input("Fecha de competición", value=None, key="fecha_competicion")
            dias_restantes = None
            if fecha_competicion:
                dias_restantes = (fecha_competicion - datetime.now(UTC).date()).days
                st.info(f"⏳ Quedan {dias_restantes} días para la competición")

        # Lesiones/molestias
        with st.expander("🤕 Lesiones / molestias"):
            lesion = st.text_input("Descripción de la lesión o molestia", key="lesion_text")

        # Comentarios opcionales
        with st.expander("📝 Notas adicionales"):
            add_comment = st.checkbox("Añadir comentario", key="add_comment_checkbox")
            comentario_extra = None
            if add_comment:
                comentario_extra = st.text_area("Escribe tu comentario", key="comentario_extra")

        # Botón de envío
        submitted = st.form_submit_button("Guardar estado")
        if submitted:
            sql.crear_evento_calendario(
                id_atleta=id_atleta,
                fecha=datetime.combine(fecha, datetime.min.time(), tzinfo=UTC),
                tipo_evento="estado_diario",
                valor={
                    "sintomas": sintomas,
                    "menstruacion": menstruacion,
                    "ovulacion": ovulacion,
                    "altitud": altitud,
                    "calor": calor,
                    "respiratorio": respiratorio,
                    "cita_test": cita_test,
                    "fecha_competicion": str(fecha_competicion) if fecha_competicion else None,
                    "dias_restantes": dias_restantes,
                    "lesion": lesion,
                    "comentario_extra": comentario_extra,
                },
                notas=None
            )
            st.success("✅ Estado diario registrado correctamente")

    st.markdown("---")

    # ───────────────────────────────
    # Eventos del calendario (incluye competiciones con contador)
    # ───────────────────────────────
    st.subheader("📌 Eventos del calendario")

    eventos = sql.obtener_eventos_por_atleta(id_atleta)
    if not eventos:
        st.info("No hay eventos registrados todavía")
    else:
        vista = st.radio("Formato de visualización", ["Tabla", "Tarjetas", "Calendario"], horizontal=True)

        # Construcción de data
        data = []
        for e in eventos:
            try:
                valor = json.loads(e.valor) if e.valor else {}
            except Exception:
                valor = {}

            fila = {
                "Fecha": e.fecha.strftime("%Y-%m-%d"),
                "Tipo": e.tipo_evento,
                "Notas": e.notas or ""
            }

            if valor.get("fecha_competicion"):
                try:
                    fecha_comp = date.fromisoformat(valor["fecha_competicion"])
                    dias_restantes = (fecha_comp - date.today()).days
                    if dias_restantes <= 7:
                        fila["Competición"] = f"<span style='color:red; font-weight:bold'>{fecha_comp} (faltan {dias_restantes} días)</span>"
                    elif dias_restantes <= 30:
                        fila["Competición"] = f"<span style='color:orange'>{fecha_comp} (faltan {dias_restantes} días)</span>"
                    else:
                        fila["Competición"] = f"{fecha_comp} (faltan {dias_restantes} días)"
                except Exception:
                    fila["Competición"] = valor["fecha_competicion"]

            if "sintomas" in valor:
                fila["Síntomas"] = valor["sintomas"]
            if "menstruacion" in valor:
                fila["Menstruacion"] = valor["menstruacion"]
            if "ovulacion" in valor:
                fila["Ovulacion"] = valor["ovulacion"]
            if "altitud" in valor:
                fila["Altitud"] = "Sí" if valor["altitud"] else "No"
            if "respiratorio" in valor:
                fila["Respiratorio"] = "Sí" if valor["respiratorio"] else "No"
            if "calor" in valor:
                fila["Calor"] = "Sí" if valor["calor"] else "No"
            if "lesion" in valor and valor["lesion"]:
                fila["Lesión"] = valor["lesion"]
            if "comentario_extra" in valor and valor["comentario_extra"]:
                fila["Comentario"] = valor["comentario_extra"]
            if "cita_test" in valor:
                fila["Cita_test"] = valor["cita_test"]

            data.append(fila)

        # Vista tabla
        if vista == "Tabla":
            df = pd.DataFrame(data)

            # Reemplazar NaN/None por guiones
            df = df.fillna("-")

            # Convertimos a HTML para poder usar estilos y badges
            def style_cell(val, col):
                if col == "Competición" and isinstance(val, str):
                    if "faltan" in val:
                        try:
                            dias = int(val.split("faltan")[1].split("días")[0])
                            if dias <= 7:
                                return f"<span style='color:red; font-weight:bold'>{val}</span>"
                            elif dias <= 30:
                                return f"<span style='color:orange'>{val}</span>"
                        except Exception:
                            return val
                if col in ["Altitud", "Respiratorio", "Calor"]:
                    if val == "Sí":
                        color = "#d4edda" if col == "Respiratorio" else "#d1ecf1" if col == "Altitud" else "#f8d7da"
                        text_color = "#155724" if col == "Respiratorio" else "#0c5460" if col == "Altitud" else "#721c24"
                        return f"<span style='background-color:{color}; color:{text_color}; padding:2px 6px; border-radius:8px;'>{val}</span>"
                if col == "Ovulacion" and val == "Confirmada":
                    return f"<span style='background-color:#ffcccc; color:#900; padding:2px 6px; border-radius:8px;'>{val}</span>"
                if col == "Lesión" and val and val != "-":
                    return f"<span style='background-color:#ffeeba; color:#856404; padding:2px 6px; border-radius:8px;'>{val}</span>"
                return val if val != "nan" else "-"

            # Aplicamos estilos a cada celda
            styled_rows = []
            for _, row in df.iterrows():
                styled_row = {}
                for col, val in row.items():
                    styled_row[col] = style_cell(val, col)
                styled_rows.append(styled_row)

            styled_df = pd.DataFrame(styled_rows)

            # Renderizamos como tabla HTML con estilos
            st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Vista tarjetas (3 columnas con fecha arriba)
        elif vista == "Tarjetas":
            for fila in data:
                # Normalizar valores vacíos a "-"
                fila = {k: ("-" if (v is None or v == "" or str(v).lower() == "nan") else v) for k, v in fila.items()}

                st.markdown(f"### 📅 {fila['Fecha']}")
                col1, col2, col3 = st.columns(3)

                # Columna 1 → Estado diario
                with col1:
                    st.markdown("#### 🧍 Estado diario")
                    st.markdown(f"- **Síntomas**: {fila.get('Síntomas','-')}")
                    st.markdown(f"- **Menstruación**: {fila.get('Menstruacion','-')}")
                    st.markdown(f"- **Ovulación**: {fila.get('Ovulacion','-')}")
                    if "Lesión" in fila:
                        st.markdown(badge("Lesión activa", "#ffeeba", "#856404"), unsafe_allow_html=True)
                        st.markdown(f"- {fila['Lesión']}")
                    if "Comentario" in fila:
                        st.markdown(f"- 📝 {fila['Comentario']}")

                # Columna 2 → Entrenamiento
                with col2:
                    st.markdown("#### 🏋️ Entrenamiento")
                    if fila.get("Altitud") == "Sí":
                        st.markdown(badge("⛰️ Altitud", "#d1ecf1", "#0c5460"), unsafe_allow_html=True)
                    if fila.get("Respiratorio") == "Sí":
                        st.markdown(badge("🌬️ Respiratorio", "#d4edda", "#155724"), unsafe_allow_html=True)
                    if fila.get("Calor") == "Sí":
                        st.markdown(badge("🔥 Calor", "#f8d7da", "#721c24"), unsafe_allow_html=True)

                # Columna 3 → Eventos
                with col3:
                    st.markdown("#### 📅 Eventos")
                    if "Cita_test" in fila:
                        st.markdown(f"- 📌 {fila['Cita_test']}")
                    if "Competición" in fila:
                        st.markdown(f"- 🏆 {fila['Competición']}", unsafe_allow_html=True)

                st.markdown("---")

        # Vista calendario interactivo
        elif vista == "Calendario":
            from src.interfaz.componentes.calendario_interactivo import mostrar_calendario_interactivo
            mostrar_calendario_interactivo(data)

    # ───────────────────────────────
    # Sesiones del día (planificado vs completado)
    # ───────────────────────────────
    st.subheader("🏃 Sesiones del día")
    sesiones = sql.obtener_sesiones_por_atleta(id_atleta)
    if not sesiones:
        st.info("No hay sesiones registradas todavía")
    else:
        df_sesiones = pd.DataFrame([{
            "Fecha": s.fecha.strftime("%Y-%m-%d"),
            "Tipo": s.tipo_sesion,
            "Planificado": s.planificado_json,
            "Realizado": s.realizado_json
        } for s in sesiones])
        st.dataframe(df_sesiones, use_container_width=True)

    st.markdown("---")

    # ───────────────────────────────
    # Métricas rápidas (entrada + gráficas placeholder)
    # ───────────────────────────────
    st.subheader("📊 Métricas rápidas")

    col1, col2 = st.columns(2)
    with col1:
        hrv = st.number_input("HRV (ms)", min_value=0, step=1)
        wellness = st.slider("Wellness (1-10)", 1, 10, 5)
    with col2:
        rpe = st.slider("RPE (1-10)", 1, 10, 5)

    if st.button("Guardar métricas rápidas"):
        sql.crear_metrica(id_atleta, "hrv", hrv, "ms")
        sql.crear_metrica(id_atleta, "wellness", wellness, "score")
        sql.crear_metrica(id_atleta, "rpe", rpe, "score")
        st.success("✅ Métricas guardadas")

    st.info("📈 Aquí se mostrarán las gráficas históricas de HRV, Wellness, RPE, Peso y FC reposo")

    st.markdown("---")

    # ───────────────────────────────
    # Notas privadas (comentarios)
    # ───────────────────────────────
    st.subheader("💬 Notas privadas (staff)")

    with st.form("form_comentario", clear_on_submit=True):
        texto = st.text_area("Comentario")
        submitted = st.form_submit_button("Guardar comentario")
        if submitted and texto.strip():
            sql.crear_comentario(id_atleta=id_atleta, texto=texto, visible_para="staff")
            st.success("✅ Comentario guardado")

    comentarios = sql.obtener_comentarios_por_atleta(id_atleta)
    if comentarios:
        st.write("### Comentarios existentes")
        for c in comentarios:
            st.markdown(f"- {c.texto} (autor {c.id_autor}, visible para {c.visible_para})")