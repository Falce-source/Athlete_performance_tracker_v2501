import streamlit as st
from src.interfaz import perfil
from src.interfaz import eventos  # ← nuevo

# ─────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Athlete Performance Tracker v2501",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# NAVEGACIÓN LATERAL
# ─────────────────────────────────────────────
st.sidebar.title("🏋️ Athlete Performance Tracker")
opcion = st.sidebar.radio(
    "Navegación",
    [
        "🏠 Inicio",
        "👤 Perfil atleta",
        "📅 Eventos",            # ← nuevo
        # Aquí podrás añadir más secciones:
        # "📅 Calendario",
        # "📊 Métricas",
        # "⚙️ Configuración"
    ]
)

# ─────────────────────────────────────────────
# CONTENIDO PRINCIPAL
# ─────────────────────────────────────────────
if opcion == "🏠 Inicio":
    st.title("Athlete Performance Tracker v2501")
    st.write("Bienvenido. Selecciona una sección en el menú lateral.")

elif opcion == "👤 Perfil atleta":
    perfil.mostrar_perfil()

elif opcion == "📅 Eventos":  # ← nuevo
    eventos.mostrar_eventos()