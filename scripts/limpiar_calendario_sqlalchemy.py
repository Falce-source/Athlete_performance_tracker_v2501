import json
from src.persistencia.sql import SessionLocal, CalendarioEvento

def normalize_details(details: dict) -> dict:
    """Convierte cualquier valor no serializable en string seguro."""
    safe = {}
    for k, v in (details or {}).items():
        if v is None:
            continue
        try:
            json.dumps(v)  # si es serializable, lo dejamos
            safe[k] = v
        except TypeError:
            safe[k] = str(v)
    return safe

def limpiar_eventos():
    with SessionLocal() as session:
        eventos = session.query(CalendarioEvento).all()
        corregidos = 0

        for ev in eventos:
            try:
                props = json.loads(ev.valor) if ev.valor else {}
            except Exception:
                continue

            if "function" in str(props):
                print(f"⚠️ Corrigiendo evento {ev.id_evento}")
                ev.valor = json.dumps(normalize_details(props))
                corregidos += 1

        session.commit()
        print(f"✅ Limpieza completada. Eventos corregidos: {corregidos}")

if __name__ == "__main__":
    limpiar_eventos()