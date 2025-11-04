import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

RUTA_LOG = "/tmp/validaciones_log.json"  # ← compatible con Cloud

def registrar_validacion(modulo, estado, backup=None):
    entrada = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "modulo": modulo,
        "estado": estado,
        "backup": backup or "-"
    }

    try:
        if os.path.exists(RUTA_LOG):
            with open(RUTA_LOG, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

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

        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.sort_values("fecha", ascending=False)
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al cargar historial: {e}")