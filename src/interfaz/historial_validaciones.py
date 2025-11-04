import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

RUTA_LOG = "validaciones_log.json"

def registrar_validacion(modulo, estado, backup=None):
    entrada = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "modulo": modulo,
        "estado": estado,
        "backup": backup or "-"
    }

    if os.path.exists(RUTA_LOG):
        with open(RUTA_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entrada)

    with open(RUTA_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def mostrar_historial():
    st.header("📈 Historial de Validaciones")

    if os.path.exists(RUTA_LOG):
        with open(RUTA_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.sort_values("fecha", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay validaciones registradas aún.")