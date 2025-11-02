import streamlit as st
import datetime
import calendar

def badge(text, color="#eee", text_color="#000"):
    """Devuelve un span HTML con estilo tipo chip/badge."""
    return f"<span style='background-color:{color}; color:{text_color}; padding:2px 6px; border-radius:8px; font-size:85%'>{text}</span>"

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
                            chips = []

                            # Estado diario
                            if ev.get("Síntomas") and ev["Síntomas"] != "-":
                                chips.append(badge(f"🧍 {ev['Síntomas']}", "#e2e3e5", "#383d41"))
                            if ev.get("Menstruacion") and ev["Menstruacion"] != "-":
                                chips.append(badge(f"🩸 {ev['Menstruacion']}", "#f8d7da", "#721c24"))
                            if ev.get("Ovulacion") and ev["Ovulacion"] != "-":
                                chips.append(badge(f"🔄 {ev['Ovulacion']}", "#d1ecf1", "#0c5460"))
                            if ev.get("Lesión") and ev["Lesión"] != "-":
                                chips.append(badge(f"🤕 {ev['Lesión']}", "#ffeeba", "#856404"))
                            if ev.get("Comentario") and ev["Comentario"] != "-":
                                chips.append(badge(f"📝 {ev['Comentario']}", "#fefefe", "#333"))

                            # Entrenamiento
                            if ev.get("Altitud") == "Sí":
                                chips.append(badge("⛰️ Altitud", "#d1ecf1", "#0c5460"))
                            if ev.get("Respiratorio") == "Sí":
                                chips.append(badge("🌬️ Respiratorio", "#d4edda", "#155724"))
                            if ev.get("Calor") == "Sí":
                                chips.append(badge("🔥 Calor", "#f8d7da", "#721c24"))

                            # Eventos especiales
                            if ev.get("Cita_test") and ev["Cita_test"] != "No":
                                chips.append(badge(f"📌 {ev['Cita_test']}", "#e2e3e5", "#383d41"))
                            if ev.get("Competición"):
                                chips.append(badge(f"🏆 {ev['Competición']}", "#fff3cd", "#856404"))

                            # Sesiones
                            if ev.get("Tipo") == "sesion":
                                chips.append(badge(f"🏃 {ev.get('Sesion_tipo','')}", "#cce5ff", "#004085"))

                            # Renderizar todos los chips en línea
                            if chips:
                                st.markdown(" ".join(chips), unsafe_allow_html=True)