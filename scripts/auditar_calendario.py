import json
from src.persistencia.sql import SessionLocal, CalendarioEvento

def auditar_eventos():
    with SessionLocal() as session:
        eventos = session.query(CalendarioEvento).all()
        sospechosos = []
        for ev in eventos:
            try:
                props = json.loads(ev.valor) if ev.valor else {}
            except Exception:
                continue
            if "function" in str(props):
                sospechosos.append((ev.id_evento, ev.valor))
        print("📋 Eventos sospechosos encontrados:")
        for ev_id, valor in sospechosos:
            print(f" - id_evento={ev_id}, valor={valor}")
        print(f"Total: {len(sospechosos)}")

if __name__ == "__main__":
    auditar_eventos()