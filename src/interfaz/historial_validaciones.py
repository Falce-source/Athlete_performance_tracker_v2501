import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

RUTA_LOG = "/tmp/validaciones_log.json"  # ← compatible con Cloud

def registrar_validacion(modulo, resultado, backup_generado=None, rol_actual=None):
    import src.persistencia.sql as sql
    texto = f"{resultado}"
    if backup_generado:
        texto += f" | Backup: {backup_generado}"
    if rol_actual:
        texto += f" | Rol: {rol_actual}"
    sql.crear_comentario(id_atleta=0, texto=texto, visible_para="staff", id_autor=None)

    try:
        if os.path.exists(RUTA_LOG):
            with open(RUTA_LOG, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Normalizar claves faltantes
            for entrada in data:
                entrada.setdefault("resultado", "-")
                entrada.setdefault("backup", "-")
                entrada.setdefault("rol", "-")
        else:
            data = []

        entrada = {
            "fecha": datetime.now().isoformat(),
            "modulo": modulo,
            "resultado": resultado,
            "backup": backup_generado or "-",
            "rol": rol_actual or "-"
        }
        data.append(entrada)

        with open(RUTA_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        st.error(f"❌ Error al registrar validación: {e}")

def mostrar_historial():
    st.header("📈 Historial de Validaciones")

    if not os.path.exists(RUTA_LOG):
        st.info("No hay validaciones registradas aún.")
        return

    try:
        with open(RUTA_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            st.info("No hay validaciones registradas aún.")
            return

        # Asegurar que todas las entradas tienen las claves necesarias
        for entrada in data:
            entrada.setdefault("fecha", datetime.now().isoformat())
            entrada.setdefault("modulo", "-")
            entrada.setdefault("resultado", "-")
            entrada.setdefault("backup", "-")
            entrada.setdefault("rol", "-")

        # Crear DataFrame con columnas garantizadas
        df = pd.DataFrame(data, columns=["fecha", "modulo", "resultado", "backup", "rol"])
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        df = df.sort_values("fecha", ascending=False)

        st.dataframe(df[["fecha", "modulo", "resultado", "backup", "rol"]], width="stretch")

        # ───────────────────────────────
        # Filtros interactivos
        # ───────────────────────────────
        st.subheader("🔎 Filtros")
        modulos = sorted(df["modulo"].unique())
        roles = sorted(df["rol"].dropna().unique())

        modulo_sel = st.selectbox("Filtrar por módulo:", ["Todos"] + modulos)
        rol_sel = st.selectbox("Filtrar por rol:", ["Todos"] + roles)
        fecha_min = st.date_input("Desde:", value=df["fecha"].min().date())
        fecha_max = st.date_input("Hasta:", value=df["fecha"].max().date())

        df_filtrado = df[
            (df["fecha"].dt.date >= fecha_min) &
            (df["fecha"].dt.date <= fecha_max)
        ]
        if modulo_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["modulo"] == modulo_sel]
        if rol_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["rol"] == rol_sel]

        st.dataframe(df_filtrado[["fecha", "modulo", "resultado", "backup", "rol"]], width="stretch")

    except Exception as e:
        st.error(f"❌ Error al cargar historial: {e}")

    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        confirmar = st.checkbox("Confirmar limpieza")
    with col2:
        if st.button("🗑️ Limpiar historial"):
            if confirmar:
                limpiar_historial()
            else:
                st.info("Marca la casilla para confirmar antes de eliminar.")

def limpiar_historial():
    if os.path.exists(RUTA_LOG):
        os.remove(RUTA_LOG)
        st.warning("🧹 Historial de validaciones eliminado.")
    else:
        st.info("No hay historial que eliminar.")
