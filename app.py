import streamlit as st
from src.interfaz import perfil
from src.interfaz import calendario   # ← nuevo

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
        "📅 Calendario",   # ← nuevo
        # "📊 Métricas",
        # "🧪 Tests",
        # "🏋️ Fuerza",
        # "🍽️ Nutrición",
        # "💬 Comentarios",
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

elif opcion == "📅 Calendario":
    calendario.mostrar_calendario()