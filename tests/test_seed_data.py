import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import src.persistencia.sql as sql
from seed_data import run_seed

@pytest.fixture(scope="module", autouse=True)
def setup_seed():
    # Ejecuta el seed antes de los tests
    run_seed()
    yield

def test_usuarios_creados():
    usuarios = sql.obtener_usuarios()
    assert len(usuarios) >= 2
    emails = [u.email for u in usuarios]
    assert "admin@example.com" in emails
    assert "laura@example.com" in emails

def test_atletas_creados():
    atletas = sql.obtener_atletas()
    assert len(atletas) >= 2
    nombres = [a.nombre for a in atletas]
    assert "Carlos" in nombres
    assert "María" in nombres

def test_eventos_calendario_creados():
    atletas = sql.obtener_atletas()
    eventos_total = 0
    for a in atletas:
        eventos_total += len(sql.obtener_eventos_calendario_por_atleta(a.id_atleta))
    assert eventos_total >= 2

def test_sesiones_creadas():
    atletas = sql.obtener_atletas()
    sesiones_total = 0
    for a in atletas:
        sesiones_total += len(sql.obtener_sesiones_por_atleta(a.id_atleta))
    assert sesiones_total >= 1

def test_metricas_creadas():
    atletas = sql.obtener_atletas()
    metricas_total = 0
    for a in atletas:
        metricas_total += len(sql.obtener_metricas_por_tipo(a.id_atleta, "hrv"))
    assert metricas_total >= 1

def test_comentarios_creados():
    atletas = sql.obtener_atletas()
    comentarios_total = 0
    for a in atletas:
        comentarios_total += len(sql.obtener_comentarios_por_atleta(a.id_atleta))
    assert comentarios_total >= 1