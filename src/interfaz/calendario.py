import streamlit as st
import pandas as pd
from datetime import datetime, UTC, date
import src.persistencia.sql as sql
import json

# Importar control de roles
from src.utils.roles import Contexto, puede_crear_evento_calendario, puede_borrar_evento_calendario

def badge(text, color="#eee", text_color="#000"):
    """Devuelve un span HTML con estilo tipo chip/badge."""
    return f"<span style='background-color:{color}; color:{text_color}; padding:2px 6px; border-radius:8px; font-size:90%'>{text}</span>"

def mostrar_calendario(rol_actual="admin", usuario_id=None):
    st.header("📅 Calendario del atleta")

    if rol_actual in ["entrenadora", "atleta"]:
        usuarios = sql.obtener_usuarios()
        nombre_usuario = next((u.nombre for u in usuarios if u.id_usuario == usuario_id), "—")
        st.caption(f"🔐 Rol activo: {rol_actual} | Usuario: {nombre_usuario} (ID {usuario_id})")
    elif rol_actual == "admin":
        st.caption("🔐 Rol activo: admin")

    # ───────────────────────────────
    # Información de depuración extendida (solo admin)
    # ───────────────────────────────
    if rol_actual == "admin":
        import os
        import src.persistencia.backup_storage as backup_storage

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
    # Selector de entrenadora (solo admin)
    # ───────────────────────────────
    if rol_actual == "admin":
        usuarios = sql.obtener_usuarios()
        entrenadoras = [u for u in usuarios if u.rol == "entrenadora"]
        opciones_entrenadora = {f"{e.nombre} (ID {e.id_usuario})": e.id_usuario for e in entrenadoras}
        seleccion_entrenadora = st.selectbox("Filtrar atletas por entrenadora", list(opciones_entrenadora.keys()))
        id_entrenadora = opciones_entrenadora[seleccion_entrenadora]
    else:
        id_entrenadora = usuario_id
    if rol_actual == "entrenadora":
        atletas = sql.obtener_atletas_por_usuario(usuario_id)
    elif rol_actual == "admin":
        atletas = sql.obtener_atletas_por_usuario(id_entrenadora)  # 🔍 admin filtra por entrenadora
    else:
        atletas = sql.obtener_atletas()
    if not atletas:
        st.info("No hay atletas registrados todavía")
        return

    opciones = {f"{a.nombre} {a.apellidos or ''} (ID {a.id_atleta})": a.id_atleta for a in atletas}
    seleccion = st.selectbox("Selecciona un atleta", list(opciones.keys()))
    id_atleta = opciones[seleccion]

    # Mostrar entrenadora asociada al atleta
    atleta_obj = sql.obtener_atleta_por_id(id_atleta)
    nombre_entrenadora = atleta_obj.usuario.nombre if atleta_obj and atleta_obj.usuario else "—"
    st.caption(f"👩‍🏫 Entrenadora asignada: {nombre_entrenadora}")

    # Construir contexto de permisos base (propietario_id se ajusta por evento)
    ctx_base = Contexto(
        rol_actual=rol_actual,
        usuario_id=usuario_id or 0,
        atleta_id=id_atleta,
        propietario_id=None
    )
    st.markdown("---")

    # ───────────────────────────────
    # Eventos del calendario
    # ───────────────────────────────
    st.subheader("🗓️ Calendario")

    # ───────────────────────────────
    # Controles de filtrado dinámico
    # ───────────────────────────────
    tipos = st.multiselect("Filtrar por tipo de evento", ["estado_diario", "competicion", "cita_test", "metricas_rapidas"])
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=None)
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=None)

    eventos = sql.obtener_eventos_filtrados(
        id_atleta=id_atleta,
        rol_actual=rol_actual,
        tipos=tipos,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    vista = st.radio(
        " ", ["Calendario", "Tabla"],
        horizontal=True, index=0,
        label_visibility="collapsed"
    )

    data = []
    eventos_fc = []
    for e in eventos:
        valor = e.get("extendedProps", {}) or {}

        fila = {
            "id_evento": e["id"],
            "Fecha": e["start"],  # string ISO
            "Tipo": e["tipo_evento"],
            "Notas": e.get("notas", ""),
            "Entrenadora": nombre_entrenadora
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
                "extendedProps": {**valor, "entrenadora": nombre_entrenadora}
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
        # Métricas rápidas
        elif tipo == "metricas_rapidas":
            # Añadimos iconos y valores a la fila de tabla
            if valor.get("hrv"): fila["HRV"] = f"💓 {valor['hrv']}"
            if valor.get("wellness"): fila["Wellness"] = f"🌟 {valor['wellness']}"
            if valor.get("rpe"): fila["RPE"] = f"💪 {valor['rpe']}"
            if valor.get("peso"): fila["Peso"] = f"⚖️ {valor['peso']}"
            if valor.get("fc_reposo"): fila["FC reposo"] = f"❤️ {valor['fc_reposo']}"

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
            if col == "HRV" and val not in ["-", ""]:
                return f"<span style='background-color:#E6F0FF; color:#0B3A82; padding:2px 6px; border-radius:8px;'>{val}</span>"
            if col == "Wellness" and val not in ["-", ""]:
                return f"<span style='background-color:#E0F7FA; color:#065F46; padding:2px 6px; border-radius:8px;'>{val}</span>"
            if col == "RPE" and val not in ["-", ""]:
                return f"<span style='background-color:#FFF4E5; color:#7C2D12; padding:2px 6px; border-radius:8px;'>{val}</span>"
            if col == "Peso" and val not in ["-", ""]:
                return f"<span style='background-color:#F3F4F6; color:#374151; padding:2px 6px; border-radius:8px;'>{val}</span>"
            if col == "FC reposo" and val not in ["-", ""]:
                return f"<span style='background-color:#FEE2E2; color:#7A1D1D; padding:2px 6px; border-radius:8px;'>{val}</span>"
            return val if val != "nan" else "-"
            return val if val != "nan" else "-"

        # Renderizado fila a fila con botón de borrado
        # Estilos CSS para fijar ancho de celdas
        table_style = """
        <style>
        .fixed-table td {
            width: 120px;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            vertical-align: middle;
        }
        .fixed-table th {
            width: 120px;
        }
        </style>
        """
        st.markdown(table_style, unsafe_allow_html=True)

        for _, row in df.iterrows():
            cols = st.columns([8, 1])  # 8 partes para datos, 1 para botón
            with cols[0]:
                styled_row = {col: style_cell(val, col) for col, val in row.items() if col != "id_evento"}
                st.markdown(
                    pd.DataFrame([styled_row]).to_html(
                        escape=False, index=False, header=False, classes="fixed-table"
                    ),
                    unsafe_allow_html=True
                )
            with cols[1]:
                # Determinar propietario real del evento (si está en datos)
                propietario_evento = e.get("id_autor") or id_atleta

                ctx_evento = Contexto(
                    rol_actual=rol_actual,
                    usuario_id=usuario_id or 0,
                    atleta_id=id_atleta,
                    propietario_id=propietario_evento
                )

                # Admin siempre puede borrar
                if rol_actual == "admin" or puede_borrar_evento_calendario(ctx_evento):
                    if st.button("🗑️", key=f"del_{row['id_evento']}"):
                        sql.borrar_evento_calendario(int(row["id_evento"]))
                        st.success(f"Evento {row['id_evento']} eliminado")
                        st.rerun()
                else:
                    st.caption("⛔ Sin permiso para borrar")

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
        st.dataframe(df_sesiones, width="stretch")

    st.markdown("---")

    # ───────────────────────────────
    # Métricas rápidas (gráficas históricas)
    # ───────────────────────────────
    st.subheader("📊 Métricas rápidas")

    import altair as alt
    metricas = sql.obtener_metricas_rapidas(id_atleta)
    if not metricas:
        st.info("No hay métricas rápidas registradas todavía")
    else:
        df_metricas = pd.DataFrame([{
            "fecha": m.fecha,  # dejamos datetime completo aquí
            "tipo": m.tipo_metrica,
            "valor": float(m.valor) if str(m.valor).replace('.','',1).isdigit() else None,
            "unidad": m.unidad
        } for m in metricas if m.valor is not None])
        # 🔧 Normalizar a inicio de día y asegurar dtype datetime64[ns]
        df_metricas["fecha"] = pd.to_datetime(df_metricas["fecha"]).dt.floor("D")
        df_metricas = df_metricas.sort_values("fecha")

        # 🔑 Ordenar cronológicamente (ya no hace falta agrupar porque sql.py garantiza unicidad)
        df_metricas = df_metricas.sort_values("fecha")

        tipos = df_metricas["tipo"].unique()
        for t in tipos:
            df_t = df_metricas[df_metricas["tipo"] == t]
            chart = alt.Chart(df_t).mark_line(point=True).encode(
                x=alt.X("fecha:T",
                        title="Día",
                        axis=alt.Axis(format="%d %b", tickCount="day")),
                y=alt.Y("valor:Q", title=f"{t.upper()}"),
                tooltip=[alt.Tooltip("fecha:T", title="Día"), "valor:Q", "unidad:N"]
            ).properties(
                title=f"{t.upper()} ({df_t['unidad'].iloc[0]})",
                width="container",
                height=200
            )
            st.altair_chart(chart, width='stretch')

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
        # Solo permitir crear evento de prueba si el rol tiene permiso
        ctx_creacion = Contexto(
            rol_actual=rol_actual,
            usuario_id=usuario_id or 0,
            atleta_id=id_atleta,
            propietario_id=id_atleta
        )
        if puede_crear_evento_calendario(ctx_creacion):
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
        else:
            st.caption("⛔ Sin permiso para crear eventos de prueba")

        if st.button("Listar eventos actuales"):
            eventos = sql.obtener_eventos_calendario_por_atleta(id_atleta, rol_actual="admin")
            st.json(eventos)

    # Prueba
    st.subheader("🗑️ Reset total de métricas rápidas (uso único)")
    if st.button("Eliminar TODO lo de métricas rápidas"):
        sql.reset_metricas_rapidas(id_atleta)
        st.success("✅ Reset completado. Se han eliminado todas las métricas rápidas y sus eventos de calendario.")
        st.rerun()
    # ----