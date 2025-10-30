import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.persistencia.sql import (
    init_db, crear_usuario, crear_atleta,
    obtener_usuarios, obtener_atletas,
    actualizar_atleta, borrar_atleta
)

def test_inicializacion_db():
    if os.path.exists("base.db"):
        os.remove("base.db")
    init_db()
    assert os.path.exists("base.db")
    print("✅ Base de datos creada correctamente")

def test_crear_usuario_y_atleta():
    usuario = crear_usuario("Ana", "ana@example.com", "entrenadora")
    assert usuario.id_usuario is not None
    assert usuario.nombre == "Ana"
    assert usuario.rol == "entrenadora"

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
    assert atleta.nombre == "Carlos"
    # Validamos con la FK directamente para evitar lazy load
    assert atleta.id_usuario == usuario.id_usuario
    print("✅ Usuario y atleta creados correctamente")

def test_listar_y_actualizar_atleta():
    atletas = obtener_atletas()
    assert len(atletas) > 0
    atleta = atletas[0]
    nivel_original = atleta.nivel

    actualizado = actualizar_atleta(atleta.id_atleta, "nivel", "Elite")
    assert actualizado.nivel == "Elite"
    print(f"✅ Atleta actualizado correctamente: {nivel_original} → {actualizado.nivel}")

def test_borrar_atleta():
    atletas = obtener_atletas()
    atleta = atletas[-1]
    borrar_atleta(atleta.id_atleta)

    ids_restantes = [a.id_atleta for a in obtener_atletas()]
    assert atleta.id_atleta not in ids_restantes
    print(f"✅ Atleta eliminado correctamente: {atleta.nombre}")

if __name__ == "__main__":
    test_inicializacion_db()
    test_crear_usuario_y_atleta()
    test_listar_y_actualizar_atleta()
    test_borrar_atleta()