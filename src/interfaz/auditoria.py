import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from src.persistencia import sql
import backup_storage

def probar_flujo(modulo):
    resultado = {"ok": False, "mensaje": "", "backup_creado": None}

    try:
        backups_antes = backup_storage.listar_backups()
        ids_antes = {b["id"] for b in backups_antes}

        if modulo == "Usuarios":
            usuario = sql.crear_usuario("TestUser", f"test_{int(time.time())}@mail.com", "admin")
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

    return resultado

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
        {"Módulo": "Eventos", "Archivo": "calendario.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "⚠️ Agrupación pendiente"},
        {"Módulo": "Sesiones", "Archivo": "sesiones.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "⚠️ Sin vista detallada"},
        {"Módulo": "Métricas", "Archivo": "metricas.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "⚠️ Sin gráfico aún"},
        {"Módulo": "Comentarios", "Archivo": "comentarios.py", "Crear": "✅", "Leer": "✅", "Actualizar": "✅", "Eliminar": "✅", "Backup": "✅", "Visual": "⚠️ Sin filtro por visibilidad"},
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

    st.markdown("---")
    st.caption("✅ = validado | ⚠️ = parcial | ❌ = pendiente")