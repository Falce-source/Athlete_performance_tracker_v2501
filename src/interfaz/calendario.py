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
    # Eventos del calendario (incluye competiciones con contador)
    # ───────────────────────────────
    st.subheader("🗓️ Calendario")

    eventos = sql.obtener_eventos_por_atleta(id_atleta)
    if not eventos:
        st.info("No hay eventos registrados todavía")
    else:
        vista = st.radio("", ["Calendario", "Tabla"], horizontal=True, index=0)

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
            df = pd.DataFrame(data).fillna("-")

            # Mapeo de estilos coherente con calendario_interactivo
            def style_cell(val, col):
                if col == "Competición" and isinstance(val, str) and "días" in val:
                    try:
                        dias = int(val.split()[0])
                        if dias <= 7:
                            return f"<span style='background-color:#FDE2E2; color:#7A1D1D; font-weight:bold; padding:2px 6px; border-radius:8px;'>{val}</span>"
                        elif dias <= 30:
                            return f"<span style='background-color:#FFF4E5; color:#7C2D12; padding:2px 6px; border-radius:8px;'>{val}</span>"
                        else:
                            return f"<span style='background-color:#F3F4F6; color:#374151; padding:2px 6px; border-radius:8px;'>{val}</span>"
                    except Exception:
                        return val
                if col == "Síntomas" and val not in ["-", "Ninguno"]:
                    return f"<span style='background-color:#FDE2E2; color:#7A1D1D; padding:2px 6px; border-radius:8px;'>🩸 {val}</span>"
                if col == "Menstruacion" and val not in ["-", "No"]:
                    return f"<span style='background-color:#FEE2E2; color:#7A1D1D; padding:2px 6px; border-radius:8px;'>🩸 {val}</span>"
                if col == "Ovulacion" and val not in ["-", "No"]:
                    return f"<span style='background-color:#F3E8FF; color:#2E1065; padding:2px 6px; border-radius:8px;'>🔄 {val}</span>"
                if col == "Altitud" and val == "Sí":
                    return f"<span style='background-color:#E6F0FF; color:#0B3A82; padding:2px 6px; border-radius:8px;'>⛰️ {val}</span>"
                if col == "Respiratorio" and val == "Sí":
                    return f"<span style='background-color:#E0F7FA; color:#065F46; padding:2px 6px; border-radius:8px;'>🌬️ {val}</span>"
                if col == "Calor" and val == "Sí":
                    return f"<span style='background-color:#FFF4E5; color:#7C2D12; padding:2px 6px; border-radius:8px;'>🔥 {val}</span>"
                if col == "Lesión" and val not in ["-", ""]:
                    return f"<span style='background-color:#FFF4D6; color:#7A4B00; padding:2px 6px; border-radius:8px;'>🤕 {val}</span>"
                if col == "Comentario" and val not in ["-", ""]:
                    return f"<span style='background-color:#F9FAFB; color:#374151; padding:2px 6px; border-radius:8px;'>📝 {val}</span>"
                return val if val != "nan" else "-"

            styled_rows = []
            for _, row in df.iterrows():
                styled_row = {col: style_cell(val, col) for col, val in row.items()}
                styled_rows.append(styled_row)

            styled_df = pd.DataFrame(styled_rows)
            st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Vista calendario interactivo (FullCalendar)
        if vista == "Calendario":
            from src.interfaz.componentes.calendario_interactivo import mostrar_calendario_interactivo
            mostrar_calendario_interactivo(data, id_atleta)

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