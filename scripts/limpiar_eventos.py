import json
from src.persistencia import sql

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

def limpiar_eventos_corruptos():
    eventos = sql.obtener_todos_eventos()  # ajusta al método real de tu capa de persistencia
    corregidos = 0

    for ev in eventos:
        ev_id = ev.get("id")
        details = ev.get("extendedProps", {})

        # Detectamos si hay algo sospechoso
        if "function" in str(details):
            print(f"⚠️ Evento {ev_id} corrupto: {details}")

            safe_details = normalize_details(details)

            # Actualizamos en la base de datos
            sql.actualizar_evento_calendario_por_id(
                id_evento=int(ev_id),
                valores_actualizados=safe_details,
                notas=details.get("notas")  # si tienes campo notas separado
            )
            corregidos += 1

    print(f"✅ Limpieza completada. Eventos corregidos: {corregidos}")

if __name__ == "__main__":
    limpiar_eventos_corruptos()