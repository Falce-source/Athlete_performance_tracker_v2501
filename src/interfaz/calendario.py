import streamlit as st
import pandas as pd
from datetime import datetime, UTC, date
from src.persistencia import sql
import json

def badge(text, color="#eee", text_color="#000"):
    """Devuelve un span HTML con estilo tipo chip/badge."""
    return f"<span style='background-color:{color}; color:{text_color}; padding:2px 6px; border-radius:8px; font-size:90%'>{text}</span>"

def mostrar_calendario(rol_actual="admin"):
    st.header("📅 Calendario del atleta")

    # ───────────────────────────────
    # Información de depuración extendida
    # ───────────────────────────────
    import os
    import backup_storage

    try:
        ruta_db = os.path.abspath(sql.engine.url.database)
        num_usuarios = len(sql.obtener_usuarios())
        num_atletas = len(sql.obtener_atletas())
        num_eventos = len(sql.obtener_eventos())

        backups = backup_storage.listar_backups()
        if backups:
            ultimo = sorted(backups, key=lambda b: b["createdTime"], reverse=True)[0]
            fecha_backup = ultimo["createdTime"]
            nombre_backup = ultimo["name"]
            backup_info = f"📦 Último backup: {nombre_backup} ({fecha_backup})"
        else:
            backup_info = "⚠️ No hay backups en Drive"

        st.info(f"🛠️ Base de datos activa: {ruta_db}")
        st.info(f"👥 Usuarios: {num_usuarios} | 🏃‍♂️ Atletas: {num_atletas} | 📅 Eventos: {num_eventos}")
        st.info(backup_info)

    except Exception as e:
        st.warning(f"No se pudo obtener información de depuración: {e}")

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
    # Eventos del calendario
    # ───────────────────────────────
    st.subheader("🗓️ Calendario")

    eventos = sql.obtener_eventos_calendario_por_atleta(id_atleta, rol_actual=rol_actual)
    vista = st.radio("", ["Calendario", "Tabla"], horizontal=True, index=0)

    data = []
    eventos_fc = []
    for e in eventos:
        valor = e.get("extendedProps", {}) or {}

        fila = {
            "id_evento": e["id"],
            "Fecha": e["start"],  # string ISO
            "Tipo": e["tipo_evento"],
            "Notas": e.get("notas", "")
        }

        # Normalizamos el tipo de evento para evitar inconsistencias
        tipo = str(e.get("tipo_evento", "")).lower().replace(" ", "_")

        # Estado diario
        if tipo == "estado_diario":
            if valor.get("sintomas") not in ["No", "-", None, "Ninguno"]:
                fila["Síntomas"] = valor.get("sintomas")
            if valor.get("menstruacion") not in ["No", "-", None]:
                fila["Menstruacion"] = valor.get("menstruacion")
            if valor.get("ovulacion") not in ["No", "-", None]:
                fila["Ovulacion"] = valor.get("ovulacion")
            if valor.get("altitud"):
                fila["Altitud"] = "Sí"
            if valor.get("respiratorio"):
                fila["Respiratorio"] = "Sí"
            if valor.get("calor"):
                fila["Calor"] = "Sí"
            if valor.get("lesion"):
                fila["Lesión"] = valor.get("lesion")
            if valor.get("comentario_extra"):
                fila["Comentario"] = valor.get("comentario_extra")

            evento_fc = {
                "id": e["id"],
                "start": e["start"],
                "allDay": True,
                "tipo_evento": tipo,          # 🔑 añade el tipo para que el otro módulo lo use
                "extendedProps": valor
            }

            eventos_fc.append(evento_fc)

        # Competición
        elif tipo == "competicion":
            try:
                fecha_comp = datetime.fromisoformat(e["start"]).date()
                dias_restantes = (fecha_comp - date.today()).days
                fila["Competición"] = f"{dias_restantes} días"
            except Exception:
                fila["Competición"] = "-"

            evento_fc = {
                "id": e["id"],
                "start": e["start"],
                "allDay": True,
                "tipo_evento": tipo,
                "extendedProps": valor
            }
            eventos_fc.append(evento_fc)

        # Cita/Test
        elif tipo == "cita_test":
            fila["Cita/Test"] = valor.get("tipo") or "Cita/Test"

            evento_fc = {
                "id": e["id"],
                "start": e["start"],
                "allDay": True,
                "tipo_evento": tipo,
                "extendedProps": valor
            }
            eventos_fc.append(evento_fc)

        data.append(fila)

    # Vista tabla
    if vista == "Tabla":
        df = pd.DataFrame(data).fillna("-")

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

        # Renderizado fila a fila con botón de borrado
        for _, row in df.iterrows():
            cols = st.columns([8, 1])  # 8 partes para datos, 1 para botón
            with cols[0]:
                styled_row = {col: style_cell(val, col) for col, val in row.items() if col != "id_evento"}
                st.markdown(
                    pd.DataFrame([styled_row]).to_html(escape=False, index=False, header=False),
                    unsafe_allow_html=True
                )
            with cols[1]:
                if st.button("🗑️", key=f"del_{row['id_evento']}"):
                    sql.borrar_evento_calendario(int(row["id_evento"]))
                    st.success(f"Evento {row['id_evento']} eliminado")
                    st.rerun()

    # Vista calendario interactivo (FullCalendar)
    if vista == "Calendario":
        from src.interfaz.componentes.calendario_interactivo import mostrar_calendario_interactivo
        mostrar_calendario_interactivo(eventos_fc, id_atleta, vista=vista)

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

    comentarios = sql.obtener_comentarios_por_atleta(id_atleta, rol_actual=rol_actual)
    if comentarios:
        st.write("### Comentarios existentes")
        for c in comentarios:
            st.markdown(f"- {c.texto} (autor {c.id_autor}, visible para {c.visible_para})")

    # Prueba

    with st.expander("🔍 Depuración de eventos (solo pruebas)"):
        if st.button("Crear evento de prueba"):
            try:
                ev = sql.crear_estado_diario(
                    id_atleta=id_atleta,
                    fecha=date.today(),
                    valores={"sintomas": "Dolor leve", "altitud": True},
                    notas="prueba desde Streamlit"
                )
                st.success(f"✅ Evento creado con id {ev.id_evento}")
            except Exception as e:
                st.error(f"❌ Error al crear evento: {e}")

        if st.button("Listar eventos actuales"):
            eventos = sql.obtener_eventos_calendario_por_atleta(id_atleta, rol_actual="admin")
            st.json(eventos)

# --------