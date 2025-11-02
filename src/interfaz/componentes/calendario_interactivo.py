import streamlit as st
import datetime

def mostrar_calendario_interactivo(eventos):
    """
    Renderiza un calendario mensual simple con los eventos.
    `eventos` es una lista de diccionarios con al menos 'Fecha' y otros campos.
    """
    st.markdown("### 🗓️ Vista calendario (demo)")

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
    month = st.selectbox("Mes", list(range(1,13)), index=hoy.month-1)

    # Construir calendario del mes
    import calendar
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(year, month)

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day.month == month:
                    st.markdown(f"**{day.day}**")
                    if day.strftime("%Y-%m-%d") in eventos_por_fecha:
                        for ev in eventos_por_fecha[day.strftime("%Y-%m-%d")]:
                            st.markdown(f"- {ev.get('Tipo','')}")
