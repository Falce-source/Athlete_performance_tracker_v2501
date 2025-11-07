import streamlit as st
import src.persistencia.sql as sql
from src.utils.seguridad import check_password, hash_password

def login_form():
    st.header("Acceder")
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        user = sql.obtener_usuario_por_email(email.strip())
        if not user:
            st.error("Usuario no encontrado")
            return False
        if not check_password(password, user.password_hash):
            st.error("Contraseña incorrecta")
            return False

        # Guardar sesión
        st.session_state["USUARIO_ID"] = user.id_usuario
        st.session_state["ROL_ACTUAL"] = user.rol
        st.session_state["USUARIO_NOMBRE"] = user.nombre
        st.success(f"Bienvenido, {user.nombre}")
        return True
    return False

def logout():
    for k in ["USUARIO_ID", "ROL_ACTUAL", "USUARIO_NOMBRE"]:
        st.session_state.pop(k, None)
    st.success("Sesión cerrada")
    st.rerun()

def crear_usuario_admin():
    """Formulario para que el admin cree usuarios con contraseña inicial"""
    st.subheader("➕ Crear nuevo usuario")
    with st.form("crear_usuario_admin", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        email = st.text_input("Email")
        rol = st.selectbox("Rol", ["admin", "entrenadora", "atleta"])
        password = st.text_input("Contraseña inicial", type="password")
        submitted = st.form_submit_button("Crear")

    if submitted:
        if not nombre or not email or not password:
            st.error("Nombre, email y contraseña son obligatorios")
            return
        ph = hash_password(password)
        nuevo = sql.crear_usuario(nombre=nombre, email=email, rol=rol, password_hash=ph)
        st.success(f"Usuario '{nuevo.nombre}' creado con rol {rol}")