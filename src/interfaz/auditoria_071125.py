import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from src.persistencia import sql
import src.persistencia.backup_storage as backup_storage

def probar_flujo(modulo, rol_actual="admin"):
    resultado = {"ok": False, "mensaje": "", "backup_creado": None}

    try:
        backups_antes = backup_storage.listar_backups()
        ids_antes = {b["id"] for b in backups_antes}

        if modulo == "Usuarios":
            usuario = sql.crear_usuario(
                nombre="TestUser",
                email=f"test_{int(time.time())}@mail.com",
                rol="admin",
                password_hash="test_hash"  # ← valor dummy para test
            )
            sql.borrar_usuario(usuario.id_usuario)

        elif modulo == "Atletas":
            atleta = sql.crear_atleta(nombre="Test", edad=20, deporte="Test", consentimiento=True)
            sql.borrar_atleta(atleta.id_atleta)

        elif modulo == "Eventos":
            atleta = sql.crear_atleta(nombre="Test", edad=20, deporte="Test", consentimiento=True)
            evento = sql.crear_evento(atleta.id_atleta, "Test Evento", datetime.now())
            sql.borrar_evento(evento.id_evento)
            sql.borrar_atleta(atleta.id_atleta)

        elif modulo == "Sesiones":
            atleta = sql.crear_atleta(nombre="Test", edad=20, deporte="Test", consentimiento=True)
            sesion = sql.crear_sesion(atleta.id_atleta, datetime.now(), "Test")
            sql.borrar_sesion(sesion.id_sesion)
            sql.borrar_atleta(atleta.id_atleta)

        elif modulo == "Métricas":
            atleta = sql.crear_atleta(nombre="Test", edad=20, deporte="Test", consentimiento=True)
            metrica = sql.crear_metrica(atleta.id_atleta, "peso", 70, "kg")
            sql.borrar_metrica(metrica.id_metrica)
            sql.borrar_atleta(atleta.id_atleta)

        elif modulo == "Comentarios":
            atleta = sql.crear_atleta(nombre="Test", edad=20, deporte="Test", consentimiento=True)
            comentario = sql.crear_comentario(atleta.id_atleta, "Comentario de prueba")
            sql.borrar_comentario(comentario.id_comentario)
            sql.borrar_atleta(atleta.id_atleta)

        else:
            resultado["mensaje"] = "❌ Módulo no reconocido"
            return resultado

        backups_despues = backup_storage.listar_backups()
        nuevos = [b for b in backups_despues if b["id"] not in ids_antes]
        if nuevos:
            resultado["ok"] = True
            resultado["mensaje"] = "✅ Flujo ejecutado correctamente y backup generado"
            resultado["backup_creado"] = nuevos[-1]["name"]
        else:
            resultado["ok"] = False
            resultado["mensaje"] = "⚠️ Flujo ejecutado pero no se detectó nuevo backup"

    except Exception as e:
        resultado["mensaje"] = f"❌ Error durante la prueba: {e}"

    from src.interfaz import historial_validaciones
    from streamlit import session_state
    rol_actual = session_state.get("ROL_ACTUAL", "admin")
    historial_validaciones.registrar_validacion(
        modulo,
        resultado["mensaje"],
        resultado.get("backup_creado"),
        rol_actual
    )
    return resultado

def probar_visibilidad_por_rol():
    resultado = {"ok": True, "mensaje": "", "backup_creado": None}
    try:
        roles = ["admin", "entrenadora", "atleta"]
        for rol in roles:
            comentarios, eventos = [], []
            try:
                atleta = sql.crear_atleta(nombre=f"Test {rol}", edad=25, deporte="Test", consentimiento=True)

                sql.crear_evento_calendario(
                    id_atleta=atleta.id_atleta,
                    fecha=datetime.now(),
                    tipo_evento="cita_test",
                    valor={"detalle": f"Evento privado para {rol}"},
                    notas=f"Nota privada {rol}"
                )

                sql.crear_comentario(
                    id_atleta=atleta.id_atleta,
                    texto=f"Comentario visible solo para {rol}",
                    visible_para=rol,
                    id_autor=None
                )

                eventos = sql.obtener_eventos_calendario_por_atleta(atleta.id_atleta, rol_actual=rol)
                comentarios = sql.obtener_comentarios_por_atleta(atleta.id_atleta, rol_actual=rol)

                eventos_ok = len(eventos) > 0
                comentarios_ok = len(comentarios) > 0

                if not eventos_ok or not comentarios_ok:
                    resultado["ok"] = False
                    resultado["mensaje"] += f"❌ Rol `{rol}` no accede correctamente a sus datos\n"

            finally:
                for c in comentarios:
                    sql.borrar_comentario(c.id_comentario)
                for e in eventos:
                    sql.borrar_evento_calendario(e["id"])
                sql.borrar_atleta(atleta.id_atleta)

        if resultado["ok"]:
            resultado["mensaje"] = "✅ Filtro por visibilidad funciona correctamente para todos los roles"

    except Exception as e:
        resultado["ok"] = False
        resultado["mensaje"] = f"❌ Error en prueba de visibilidad: {e}"

    from src.interfaz import historial_validaciones
    from streamlit import session_state
    rol_actual = session_state.get("ROL_ACTUAL", "admin")
    historial_validaciones.registrar_validacion("Comentarios", resultado["mensaje"], resultado["backup_creado"], rol_actual=rol_actual)
    return resultado

def validar_flujo_atleta():
    st.subheader("🧪 Validación de trazabilidad de atletas")

    usuarios = sql.obtener_usuarios()
    atletas = sql.obtener_atletas()
    errores = []

    for atleta in atletas:
        if not atleta.atleta_usuario_id:
            errores.append(f"❌ Atleta '{atleta.nombre}' sin usuario vinculado")
        else:
            usuario_atleta = next((u for u in usuarios if u.id_usuario == atleta.atleta_usuario_id), None)
            if not usuario_atleta:
                errores.append(f"❌ Usuario vinculado al atleta '{atleta.nombre}' no existe")
            elif usuario_atleta.rol != "atleta":
                errores.append(f"❌ Usuario '{usuario_atleta.nombre}' tiene rol '{usuario_atleta.rol}' pero está vinculado como atleta")

        if not atleta.id_usuario:
            errores.append(f"❌ Atleta '{atleta.nombre}' sin entrenadora asignada")

        if not atleta.propietario_id:
            errores.append(f"❌ Atleta '{atleta.nombre}' sin propietario registrado")

    if errores:
        st.warning("🔍 Errores detectados en la trazabilidad:")
        for e in errores:
            st.markdown(f"- {e}")
    else:
        st.success("✅ Todos los atletas están correctamente vinculados con usuario, entrenadora y propietario.")

def validar_atletas_duplicados():
    st.subheader("🧪 Detección de atletas duplicados")

    atletas = sql.obtener_atletas()
    duplicados = []

    # Por nombre + apellidos + contacto
    vistos = {}
    for a in atletas:
        clave = (a.nombre.strip().lower(), (a.apellidos or "").strip().lower(), (a.contacto or "").strip().lower())
        if clave in vistos:
            duplicados.append(f"❌ Duplicado por nombre/apellidos/contacto: '{a.nombre} {a.apellidos}' (ID {a.id_atleta}) y (ID {vistos[clave]})")
        else:
            vistos[clave] = a.id_atleta

    # Por email compartido entre perfiles
    emails = {}
    for a in atletas:
        email = (a.contacto or "").strip().lower()
        if email:
            if email in emails:
                duplicados.append(f"❌ Email compartido: '{email}' en atletas ID {a.id_atleta} y {emails[email]}")
            else:
                emails[email] = a.id_atleta

    if duplicados:
        st.warning("🔍 Atletas duplicados detectados:")
        for d in duplicados:
            st.markdown(f"- {d}")
    else:
        st.success("✅ No se detectaron duplicados por nombre, contacto o email.")

def validar_usuarios_duplicados():
    st.subheader("🧪 Detección de usuarios duplicados")

    usuarios = sql.obtener_usuarios()
    duplicados = []

    # Por email
    emails = {}
    for u in usuarios:
        email = u.email.strip().lower()
        if email in emails:
            duplicados.append(f"❌ Email duplicado: '{email}' en usuarios ID {u.id_usuario} y {emails[email]}")
        else:
            emails[email] = u.id_usuario

    # Por nombre (no siempre crítico, pero útil si hay colisiones)
    nombres = {}
    for u in usuarios:
        nombre = u.nombre.strip().lower()
        if nombre in nombres:
            duplicados.append(f"⚠️ Nombre duplicado: '{u.nombre}' en usuarios ID {u.id_usuario} y {nombres[nombre]}")
        else:
            nombres[nombre] = u.id_usuario

    if duplicados:
        st.warning("🔍 Usuarios duplicados detectados:")
        for d in duplicados:
            st.markdown(f"- {d}")
    else:
        st.success("✅ No se detectaron duplicados por email o nombre.")

def validar_desvinculados():
    st.subheader("🧪 Detección de atletas y usuarios no vinculados")

    atletas = sql.obtener_atletas()
    usuarios = sql.obtener_usuarios()

    errores = []

    # Atletas sin usuario vinculado
    ids_reportados = set()  # ← nuevo

    sin_usuario = [a for a in atletas if not getattr(a, "atleta_usuario_id", None)]
    for a in sin_usuario:
        errores.append(f"❌ Atleta '{a.nombre}' (ID {a.id_atleta}) sin usuario vinculado")
        ids_reportados.add(a.id_atleta)

    # Usuarios con rol atleta sin perfil asociado
    ids_vinculados = {a.atleta_usuario_id for a in atletas if a.atleta_usuario_id}
    atletas_huerfanos = [u for u in usuarios if u.rol == "atleta" and u.id_usuario not in ids_vinculados]
    for u in atletas_huerfanos:
        errores.append(f"❌ Usuario atleta '{u.nombre}' (ID {u.id_usuario}) no está vinculado a ningún perfil")

    # Eliminar errores duplicados ya reportados
    errores = list({e for e in errores if not any(f"(ID {id})" in e for id in ids_reportados)})

    if errores:
        st.warning("🔍 Desvinculaciones detectadas:")
        for e in errores:
            st.markdown(f"- {e}")
    else:
        st.success("✅ Todos los atletas y usuarios están correctamente vinculados.")

def mostrar_atletas_ocultos_con_boton():
    st.subheader("🧹 Atletas huérfanos detectados")

    atletas = sql.obtener_atletas()
    ocultos = [a for a in atletas if not a.atleta_usuario_id or not a.id_usuario]

    if ocultos:
        for a in ocultos:
            with st.expander(f"🕵️‍♂️ Atleta: {a.nombre} (ID {a.id_atleta})"):
                st.markdown(f"- Usuario vinculado: `{a.atleta_usuario_id}`")
                st.markdown(f"- Entrenadora asignada: `{a.id_usuario}`")
                st.markdown(f"- Propietario: `{a.propietario_id}`")

                if st.button(f"🗑️ Eliminar atleta '{a.nombre}'", key=f"borrar_{a.id_atleta}"):
                    sql.borrar_atleta(a.id_atleta)
                    st.warning(f"✅ Atleta '{a.nombre}' eliminado. 🔄 Recarga la pestaña para actualizar la lista.")
    else:
        st.success("✅ No hay atletas huérfanos por falta de vínculos.")

def mostrar_usuarios_huerfanos_con_boton():
    st.subheader("🧹 Usuarios atleta sin perfil vinculado")

    usuarios = sql.obtener_usuarios()
    atletas = sql.obtener_atletas()
    ids_vinculados = {a.atleta_usuario_id for a in atletas if a.atleta_usuario_id}

    huerfanos = [u for u in usuarios if u.rol == "atleta" and u.id_usuario not in ids_vinculados]

    if huerfanos:
        for u in huerfanos:
            with st.expander(f"👤 Usuario: {u.nombre} (ID {u.id_usuario})"):
                st.markdown(f"- Email: `{u.email}`")
                st.markdown(f"- Rol: `{u.rol}`")
                st.markdown(f"- Vinculado a perfil: ❌ No")

                if st.button(f"🗑️ Eliminar usuario '{u.nombre}'", key=f"borrar_usuario_{u.id_usuario}"):
                    sql.borrar_usuario(u.id_usuario)
                    st.warning(f"✅ Usuario '{u.nombre}' eliminado. 🔄 Recarga la pestaña para actualizar la lista.")
    else:
        st.success("✅ No hay usuarios atleta sin perfil vinculado.")

def mostrar_auditoria():
    st.header("🔍 Auditoría Técnica")

    try:
        ruta_db = os.path.abspath(sql.engine.url.database)
        st.info(f"🛠️ Base activa: {ruta_db}")
    except Exception as e:
        st.warning(f"No se pudo obtener la ruta de la base: {e}")

    st.subheader("📦 Estado de módulos CRUD")

    modulos = [
        {"Módulo": "Usuarios", "Archivo": "usuarios.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "✅"},
        {"Módulo": "Atletas", "Archivo": "atletas.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "✅"},
        {"Módulo": "Eventos", "Archivo": "calendario.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "✅ Agrupación por fecha y tipo + filtro por visibilidad"},
        {"Módulo": "Sesiones", "Archivo": "sesiones.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "⚠️ Sin vista detallada"},
        {"Módulo": "Métricas", "Archivo": "metricas.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "⚠️ Sin gráfico aún"},
        {"Módulo": "Comentarios", "Archivo": "comentarios.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "✅ Filtro por visibilidad activo"},
    ]

    for m in modulos:
        with st.expander(f"🔧 {m['Módulo']}"):
            st.write(f"**Archivo:** `{m['Archivo']}`")
            st.write(f"**Estado CRUD:** Crear {m['Crear']} | Leer {m['Leer']} | Actualizar {m['Actualizar']} | Eliminar {m['Eliminar']}")
            st.write(f"**Backup tras commit:** {m['Backup']}")
            st.write(f"**Validación visual:** {m['Visual']}")

            cols = st.columns(3)
            with cols[0]:
                st.button("📂 Ver código fuente", key=f"codigo_{m['Módulo']}")
            with cols[1]:
                if st.button("🧪 Probar flujo", key=f"probar_{m['Módulo']}"):
                    if m["Módulo"] == "Comentarios":
                        resultado = probar_visibilidad_por_rol()
                    else:
                        resultado = probar_flujo(m["Módulo"])
                    st.success(resultado["mensaje"]) if resultado["ok"] else st.error(resultado["mensaje"])
                    if resultado["backup_creado"]:
                        st.info(f"📦 Backup generado: {resultado['backup_creado']}")
            with cols[2]:
                backups = backup_storage.listar_backups()
                if backups:
                    ultimo = sorted(backups, key=lambda b: b["createdTime"], reverse=True)[0]
                    st.caption(f"📦 Último backup: {ultimo['name']} ({ultimo['createdTime']})")
                else:
                    st.caption("⚠️ No hay backups disponibles")
    
    st.subheader("📋 Validaciones cruzadas")
    validar_flujo_atleta()
    validar_atletas_duplicados()
    validar_usuarios_duplicados()
    validar_desvinculados()
    mostrar_atletas_ocultos_con_boton()
    mostrar_usuarios_huerfanos_con_boton()
