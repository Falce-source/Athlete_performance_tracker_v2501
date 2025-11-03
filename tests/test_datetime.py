import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import uuid
from datetime import datetime, UTC
from src.persistencia import sql

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    sql.init_db()
    yield

def test_usuario_creado_en_tz():
    email = f"fecha_{uuid.uuid4().hex}@example.com"
    u = sql.crear_usuario("FechaTest", email, "admin")
    assert isinstance(u.creado_en, datetime)
    ahora = datetime.now(UTC).replace(tzinfo=None)
    assert abs((ahora - u.creado_en).total_seconds()) < 5
    sql.borrar_usuario(u.id_usuario)

def test_atleta_creado_en_tz():
    a = sql.crear_atleta(nombre="FechaAtleta", deporte="Ciclismo")
    assert isinstance(a.creado_en, datetime)
    ahora = datetime.now(UTC).replace(tzinfo=None)
    assert abs((ahora - a.creado_en).total_seconds()) < 5
    sql.borrar_atleta(a.id_atleta)

def test_evento_creado_en_tz():
    a = sql.crear_atleta(nombre="FechaEvento", deporte="Natación")
    e = sql.crear_evento(a.id_atleta, "Entrenamiento", datetime.now(UTC))
    assert isinstance(e.creado_en, datetime)
    ahora = datetime.now(UTC).replace(tzinfo=None)
    assert abs((ahora - e.creado_en).total_seconds()) < 5
    sql.borrar_evento(e.id_evento)
    sql.borrar_atleta(a.id_atleta)

def test_calendario_evento_creado_en_tz():
    a = sql.crear_atleta(nombre="FechaCalendario", deporte="Atletismo")
    fecha = datetime.now(UTC)
    ev = sql.crear_evento_calendario(a.id_atleta, fecha, "Competición", {"dato": "ok"})
    assert isinstance(ev.creado_en, datetime)
    ahora = datetime.now(UTC).replace(tzinfo=None)
    assert abs((ahora - ev.creado_en).total_seconds()) < 5
    sql.borrar_evento_calendario(a.id_atleta, fecha)
    sql.borrar_atleta(a.id_atleta)

def test_comentario_fecha_tz():
    a = sql.crear_atleta(nombre="FechaComentario", deporte="Tenis")
    c = sql.crear_comentario(a.id_atleta, "Comentario con fecha")
    assert isinstance(c.fecha, datetime)
    ahora = datetime.now(UTC).replace(tzinfo=None)
    assert abs((ahora - c.fecha).total_seconds()) < 5
    sql.borrar_comentario(c.id_comentario)
    sql.borrar_atleta(a.id_atleta)