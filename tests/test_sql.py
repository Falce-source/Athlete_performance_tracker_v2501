import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.persistencia.sql import (
    init_db, crear_usuario, crear_atleta,
    obtener_usuarios, obtener_atletas,
    actualizar_atleta, borrar_atleta
)

def test_inicializacion_db():
    # Elimina base anterior si existe
    if os.path.exists("base.db"):
        os.remove("base.db")
    init_db()
    assert os.path.exists("base.db")
    print("✅ Base de datos creada correctamente")

def test_crear_usuario_y_atleta():
    usuario = crear_usuario("Ana", "ana@example.com", "entrenadora")
    assert usuario.id_usuario is not None

    atleta = crear_atleta(
        nombre="Carlos",
        apellidos="Pérez",
        edad=25,
        talla=178,
        contacto="carlos@example.com",
        deporte="Triatlón",
        modalidad="Sprint",
        nivel="Avanzado",
        equipo="TeamX",
        alergias="Ninguna",
        consentimiento=True,
        id_usuario=usuario.id_usuario
    )
    assert atleta.id_atleta is not None
    print("✅ Usuario y atleta creados correctamente")

def test_listar_y_actualizar_atleta():
    atletas = obtener_atletas()
    assert len(atletas) > 0
    atleta = atletas[0]

    actualizado = actualizar_atleta(atleta.id_atleta, "nivel", "Elite")
    assert actualizado.nivel == "Elite"
    print("✅ Atleta actualizado correctamente")

def test_borrar_atleta():
    atletas = obtener_atletas()
    atleta = atletas[-1]
    borrar_atleta(atleta.id_atleta)

    eliminado = any(a.id_atleta == atleta.id_atleta for a in obtener_atletas())
    assert not eliminado
    print("✅ Atleta eliminado correctamente")

if __name__ == "__main__":
    test_inicializacion_db()
    test_crear_usuario_y_atleta()
    test_listar_y_actualizar_atleta()
    test_borrar_atleta()