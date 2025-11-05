import sqlite3, json, os

# Ajusta la ruta a tu base real si trabajas en local
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "persistencia", "base.db"
)

def normalize_details(details: dict) -> dict:
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
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id_evento, valor FROM calendario_eventos")
    rows = cur.fetchall()

    corregidos = 0
    for ev_id, valor in rows:
        try:
            props = json.loads(valor) if valor else {}
        except Exception:
            continue

        if "function" in str(props):
            print(f"⚠️ Corrigiendo evento {ev_id}")
            safe = normalize_details(props)
            cur.execute(
                "UPDATE calendario_eventos SET valor=? WHERE id_evento=?",
                (json.dumps(safe), ev_id)
            )
            corregidos += 1

    conn.commit()
    conn.close()
    print(f"✅ Limpieza completada. Eventos corregidos: {corregidos}")

if __name__ == "__main__":
    limpiar_eventos()