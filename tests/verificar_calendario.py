import json
from src.persistencia.sql import SessionLocal, CalendarioEvento

def listar_eventos(id_atleta=None, limite=10):
    """
    Lista los últimos eventos del calendario.
    - id_atleta: si se pasa, filtra por ese atleta
    - limite: número máximo de registros a mostrar
    """
    with SessionLocal() as session:
        query = session.query(CalendarioEvento).order_by(CalendarioEvento.fecha.desc())
        if id_atleta is not None:
            query = query.filter_by(id_atleta=id_atleta)
        eventos = query.limit(limite).all()

        print(f"\nÚltimos {len(eventos)} eventos" + (f" para atleta {id_atleta}" if id_atleta else "") + ":")
        for ev in eventos:
            try:
                valor = json.loads(ev.valor) if ev.valor else {}
            except Exception:
                valor = ev.valor
            print(f"- ID {ev.id_evento} | Fecha: {ev.fecha} | Tipo: {ev.tipo_evento} | Valor: {valor} | Notas: {ev.notas}")

def buscar_evento(id_atleta, fecha):
    """
    Busca un evento exacto por atleta y fecha.
    """
    with SessionLocal() as session:
        ev = session.query(CalendarioEvento).filter_by(id_atleta=id_atleta, fecha=fecha).first()
        if ev:
            try:
                valor = json.loads(ev.valor) if ev.valor else {}
            except Exception:
                valor = ev.valor
            print(f"\nEvento encontrado: ID {ev.id_evento} | Fecha: {ev.fecha} | Valor: {valor}")
        else:
            print(f"\nNo se encontró evento para atleta {id_atleta} en fecha {fecha}")

if __name__ == "__main__":
    # 🔹 Ejemplos de uso:
    listar_eventos()                  # lista últimos 10 eventos globales
    listar_eventos(id_atleta=3)       # lista últimos 10 eventos de atleta 3
    # buscar_evento(3, "2025-11-03 00:00:00")  # busca un evento exacto