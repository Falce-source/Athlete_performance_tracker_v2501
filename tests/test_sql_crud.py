import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from datetime import datetime, timezone
import src.persistencia.sql as sql

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Inicializa la base de datos antes de correr los tests
    sql.init_db()
    yield

# ───────────────────────────────
# USUARIOS
# ───────────────────────────────
def test_crud_usuario():
    u = sql.crear_usuario("Test User", "test@example.com", "admin")
    assert u.id_usuario is not None

    usuarios = sql.obtener_usuarios()
    assert any(us.email == "test@example.com" for us in usuarios)

    u2 = sql.actualizar_usuario(u.id_usuario, rol="entrenador")
    assert u2.rol == "entrenador"

    sql.borrar_usuario(u.id_usuario)
    usuarios = sql.obtener_usuarios()
    assert all(us.id_usuario != u.id_usuario for us in usuarios)

# ───────────────────────────────
# ATLETAS
# ───────────────────────────────
def test_crud_atleta():
    a = sql.crear_atleta(nombre="Ana", apellidos="Prueba", edad=25, deporte="Ciclismo")
    assert a.id_atleta is not None

    atleta = sql.obtener_atleta_por_id(a.id_atleta)
    assert atleta.nombre == "Ana"

    a2 = sql.actualizar_atleta(a.id_atleta, nivel="Avanzado")
    assert a2.nivel == "Avanzado"

    sql.borrar_atleta(a.id_atleta)
    assert sql.obtener_atleta_por_id(a.id_atleta) is None

# ───────────────────────────────
# EVENTOS BÁSICOS
# ───────────────────────────────
def test_crud_evento_basico():
    a = sql.crear_atleta(nombre="Luis", deporte="Natación")
    e = sql.crear_evento(a.id_atleta, "Entrenamiento", datetime.now(timezone.utc))
    assert e.id_evento is not None

    eventos = sql.obtener_eventos_basicos_por_atleta(a.id_atleta)
    assert len(eventos) > 0

    e2 = sql.actualizar_evento(e.id_evento, lugar="Piscina")
    assert e2.lugar == "Piscina"

    sql.borrar_evento(e.id_evento)
    eventos = sql.obtener_eventos_basicos_por_atleta(a.id_atleta)
    assert all(ev.id_evento != e.id_evento for ev in eventos)

    sql.borrar_atleta(a.id_atleta)

# ───────────────────────────────
# CALENDARIO EVENTOS
# ───────────────────────────────
def test_crud_calendario_evento():
    a = sql.crear_atleta(nombre="Marta", deporte="Atletismo")
    fecha = datetime.now(timezone.utc)

    ev = sql.crear_evento_calendario(a.id_atleta, fecha, "Competición", {"fecha_competicion": fecha.isoformat()})
    assert ev.id_evento is not None

    ev2 = sql.actualizar_evento_calendario(a.id_atleta, fecha, {"sintomas": "Fatiga"})
    assert "Fatiga" in ev2.valor

    eventos = sql.obtener_eventos_calendario_por_atleta(a.id_atleta)
    assert len(eventos) == 1

    ok = sql.borrar_evento_calendario(a.id_atleta, fecha)
    assert ok is True

    sql.borrar_atleta(a.id_atleta)

# ───────────────────────────────
# SESIONES
# ───────────────────────────────
def test_crud_sesion():
    a = sql.crear_atleta(nombre="Carlos", deporte="Fútbol")
    fecha = datetime.now(timezone.utc)

    s = sql.crear_sesion(a.id_atleta, fecha, "Entrenamiento", planificado_json="Plan", realizado_json="Real")
    assert s.id_sesion is not None

    sesiones = sql.obtener_sesiones_por_atleta(a.id_atleta)
    assert len(sesiones) > 0

    s2 = sql.actualizar_sesion(s.id_sesion, realizado_json="Realizado OK")
    assert s2.realizado_json == "Realizado OK"

    sql.borrar_sesion(s.id_sesion)
    sesiones = sql.obtener_sesiones_por_atleta(a.id_atleta)
    assert all(ss.id_sesion != s.id_sesion for ss in sesiones)

    sql.borrar_atleta(a.id_atleta)

# ───────────────────────────────
# MÉTRICAS
# ───────────────────────────────
def test_crud_metrica():
    a = sql.crear_atleta(nombre="Laura", deporte="Triatlón")

    m = sql.crear_metrica(a.id_atleta, "hrv", 50, "ms")
    assert m.id_metrica is not None

    metricas = sql.obtener_metricas_por_tipo(a.id_atleta, "hrv")
    assert len(metricas) > 0

    m2 = sql.actualizar_metrica(m.id_metrica, valor="55")
    assert m2.valor == "55"

    sql.borrar_metrica(m.id_metrica)
    metricas = sql.obtener_metricas_por_tipo(a.id_atleta, "hrv")
    assert all(mm.id_metrica != m.id_metrica for mm in metricas)

    sql.borrar_atleta(a.id_atleta)

# ───────────────────────────────
# COMENTARIOS
# ───────────────────────────────
def test_crud_comentario():
    a = sql.crear_atleta(nombre="Pedro", deporte="Tenis")

    c = sql.crear_comentario(a.id_atleta, "Comentario inicial")
    assert c.id_comentario is not None

    comentarios = sql.obtener_comentarios_por_atleta(a.id_atleta)
    assert len(comentarios) > 0

    c2 = sql.actualizar_comentario(c.id_comentario, texto="Comentario editado")
    assert c2.texto == "Comentario editado"

    sql.borrar_comentario(c.id_comentario)
    comentarios = sql.obtener_comentarios_por_atleta(a.id_atleta)
    assert all(cc.id_comentario != c.id_comentario for cc in comentarios)

    sql.borrar_atleta(a.id_atleta)
