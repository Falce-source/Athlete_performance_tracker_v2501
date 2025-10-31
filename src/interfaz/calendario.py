import streamlit as st
import pandas as pd
from datetime import datetime, UTC
from src.persistencia import sql

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

        with st.expander("🩸 Datos de ciclo"):
            sintomas = st.selectbox("Síntomas menstruales", ["Ninguno", "Dolor leve", "Dolor moderado", "Dolor intenso"])
            menstruacion = st.selectbox("Menstruación", ["No", "Día 1", "Día 2", "Día 3", "Día 4+"])
            ovulacion = st.selectbox("Ovulación", ["No", "Estimada", "Confirmada"])

        # Altitud y calor como selectbox (no expander)
        altitud = st.selectbox("⛰️ Entrenamiento en altitud", ["No", "Sí"], key="altitud_select")
        calor = st.selectbox("🔥 Entrenamiento en calor", ["No", "Sí"], key="calor_select")

        with st.expander("🌬️ Entrenamiento respiratorio"):
            respiratorio = st.checkbox("Sí", key="respiratorio_checkbox")

        with st.expander("📅 Citas / Tests"):
            cita_test = st.selectbox("Selecciona", ["No", "Cita", "Test"], key="cita_test_select")

        with st.expander("🏆 Competición"):
            competicion = st.checkbox("Sí", key="competicion_checkbox")

        with st.expander("🤕 Lesiones / molestias"):
            lesion = st.text_input("Descripción de la lesión o molestia", key="lesion_text")

        with st.expander("🚫 Baja"):
            baja = st.checkbox("No entrena / compite", key="baja_checkbox")

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
                    "competicion": competicion,
                    "lesion": lesion,
                    "baja": baja,
                },
                notas=None
            )
            st.success("✅ Estado diario registrado correctamente")

    st.markdown("---")

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