import streamlit as st
import datetime
import calendar

def mostrar_calendario_interactivo(eventos):
    """
    Renderiza un calendario mensual con los eventos y sesiones.
    `eventos` es una lista de diccionarios con al menos 'Fecha' y otros campos.
    """

    st.markdown("### 🗓️ Vista calendario")

    # Agrupar eventos por fecha
    eventos_por_fecha = {}
    for e in eventos:
        fecha = e.get("Fecha")
        if fecha not in eventos_por_fecha:
            eventos_por_fecha[fecha] = []
        eventos_por_fecha[fecha].append(e)

    # Selector de mes/año
    hoy = datetime.date.today()
    year = st.selectbox("Año", [hoy.year-1, hoy.year, hoy.year+1], index=1)
    month = st.selectbox("Mes", list(range(1, 13)), index=hoy.month-1)

    # Construir calendario del mes
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(year, month)

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day.month == month:
                    st.markdown(f"**{day.day}**")

                    fecha_str = day.strftime("%Y-%m-%d")
                    if fecha_str in eventos_por_fecha:
                        for ev in eventos_por_fecha[fecha_str]:
                            detalles = []

                            # Estado diario
                            if ev.get("Síntomas") and ev["Síntomas"] != "-":
                                detalles.append(f"🧍 {ev['Síntomas']}")
                            if ev.get("Menstruacion") and ev["Menstruacion"] != "-":
                                detalles.append(f"🩸 {ev['Menstruacion']}")
                            if ev.get("Ovulacion") and ev["Ovulacion"] != "-":
                                detalles.append(f"🔄 {ev['Ovulacion']}")
                            if ev.get("Lesión") and ev["Lesión"] != "-":
                                detalles.append(f"🤕 {ev['Lesión']}")
                            if ev.get("Comentario") and ev["Comentario"] != "-":
                                detalles.append(f"📝 {ev['Comentario']}")

                            # Entrenamiento
                            if ev.get("Altitud") == "Sí":
                                detalles.append("⛰️ Altitud")
                            if ev.get("Respiratorio") == "Sí":
                                detalles.append("🌬️ Respiratorio")
                            if ev.get("Calor") == "Sí":
                                detalles.append("🔥 Calor")

                            # Eventos especiales
                            if ev.get("Cita_test") and ev["Cita_test"] != "No":
                                detalles.append(f"📌 {ev['Cita_test']}")
                            if ev.get("Competición"):
                                detalles.append(f"🏆 {ev['Competición']}")

                            # Sesiones
                            if ev.get("Tipo") == "sesion":
                                detalles.append(f"🏃 {ev.get('Sesion_tipo','')}")

                            # Renderizar todos los detalles
                            for d in detalles:
                                st.markdown(f"- {d}")