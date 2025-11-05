import sqlite3, os

# Ajusta la ruta a tu base de datos real
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "persistencia", "base.db"
)

def explorar_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print(f"📂 Explorando base de datos: {DB_PATH}\n")

    # Listar todas las tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = [t[0] for t in cur.fetchall()]
    print("Tablas encontradas:")
    for t in tablas:
        print("  -", t)

    print("\nEstructura de cada tabla:")
    for t in tablas:
        print(f"\n🔎 Tabla: {t}")
        cur.execute(f"PRAGMA table_info({t});")
        cols = cur.fetchall()
        for col in cols:
            # col = (cid, name, type, notnull, dflt_value, pk)
            print(f"   • {col[1]} ({col[2]})")

    conn.close()

if __name__ == "__main__":
    explorar_db()