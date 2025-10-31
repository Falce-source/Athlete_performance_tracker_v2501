"""
Script de carga inicial de datos de ejemplo.
Ejecutar con:  python tests/test_seed_data.py
"""

from datetime import datetime, timezone
from src.persistencia import sql

def run_seed():
    # Inicializar base limpia
    sql.init_db()

    # ───────────────────────────────
    # Crear usuarios
    # ───────────────────────────────
    admin = sql.crear_usuario(nombre="Admin", email="admin@example.com", rol="admin")
    entrenadora = sql.crear_usuario(nombre="Laura", email="laura@example.com", rol="entrenadora")

    # ───────────────────────────────
    # Crear atletas
    # ───────────────────────────────
    atleta1 = sql.crear_atleta(
        nombre="Carlos",
        apellidos="Pérez",
        edad=25,
        talla=180,
        deporte="Ciclismo",
        modalidad="Carretera",
        nivel="Avanzado",
        equipo="Team Aragón",
        consentimiento=True,
        id_usuario=entrenadora.id_usuario
    )

    atleta2 = sql.crear_atleta(
        nombre="María",
        apellidos="López",
        edad=22,
        talla=170,
        deporte="Atletismo",
        modalidad="Fondo",
        nivel="Élite",
        equipo="Club Barbastro",
        consentimiento=True,
        id_usuario=entrenadora.id_usuario
    )

    # ───────────────────────────────
    # Crear eventos de calendario
    # ───────────────────────────────
    sql.crear_evento_calendario(
        id_atleta=atleta1.id_atleta,
        fecha=datetime(2025, 10, 30, tzinfo=timezone.utc),
        tipo_evento="estado_diario",
        valor={"altitud": True, "competicion": False, "sintomas": "Ninguno"},
        notas="Entrenamiento en altura"
    )

    sql.crear_evento_calendario(
        id_atleta=atleta2.id_atleta,
        fecha=datetime(2025, 10, 29, tzinfo=timezone.utc),
        tipo_evento="estado_diario",
        valor={"menstruacion": "Día 2", "sintomas": "Dolor leve"},
        notas="Ciclo menstrual activo"
    )

    # ───────────────────────────────
    # Crear sesiones
    # ───────────────────────────────
    from src.persistencia.sql import Sesion, SessionLocal
    with SessionLocal() as session:
        sesion = Sesion(
            id_atleta=atleta1.id_atleta,
            fecha=datetime(2025, 10, 30, tzinfo=timezone.utc),
            tipo_sesion="ciclismo_carretera",
            planificado_json='{"duracion": 120, "distancia": 60, "TSS": 150}',
            realizado_json='{"duracion": 115, "distancia": 58, "TSS": 140}'
        )
        session.add(sesion)
        session.commit()

    # ───────────────────────────────
    # Crear métricas
    # ───────────────────────────────
    sql.crear_metrica(atleta1.id_atleta, "hrv", 75, "ms")
    sql.crear_metrica(atleta1.id_atleta, "wellness", 7, "score")
    sql.crear_metrica(atleta1.id_atleta, "rpe", 6, "score")

    # ───────────────────────────────
    # Crear comentarios
    # ───────────────────────────────
    sql.crear_comentario(
        id_atleta=atleta1.id_atleta,
        texto="Revisar carga de entrenamiento, parece alta.",
        visible_para="staff",
        id_autor=entrenadora.id_usuario
    )

    print("✅ Datos de ejemplo cargados correctamente.")

if __name__ == "__main__":
    run_seed()
