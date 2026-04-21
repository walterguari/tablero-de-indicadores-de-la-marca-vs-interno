import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

st.title("📊 Monitor de Calidad Total - Método NPS")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

def load_data(url):
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    df = pd.read_csv(csv_url)
    # Convertimos la columna de fecha a formato datetime de Python
    df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
    return df

def calcular_nps(serie):
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    if serie.empty: return 0
    promotores = (serie >= 9).sum()
    detractores = (serie <= 6).sum()
    total = len(serie)
    return ((promotores - detractores) / total) * 100

def crear_grafico_torta(df, columna, titulo):
    conteo = df[columna].value_counts().reset_index()
    conteo.columns = [columna, 'Cantidad']
    fig = px.pie(
        conteo, 
        values='Cantidad', 
        names=columna, 
        title=titulo,
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent+label+value')
    return fig

try:
    df = load_data(sheet_url)
    
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Búsqueda")
    
    # Filtro de Fecha
    min_date = df["Fecha de ultimo contacto"].min()
    max_date = df["Fecha de ultimo contacto"].max()
    
    date_range = st.sidebar.date_input(
        "Rango de Fechas (Ult. contacto)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
    canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())
    vendedor = st.sidebar.multiselect("Vendedor", options=df["Vendedor"].unique(), default=df["Vendedor"].unique())
    
    # Aplicar Filtros
    mask = (
        (df["MARCA"].isin(marca)) & 
        (df["Canal de Venta"].isin(canal)) & 
        (df["Vendedor"].isin(vendedor))
    )
    
    # Validar que el rango de fechas esté completo antes de filtrar
    if len(date_range) == 2:
        mask = mask & (df["Fecha de ultimo contacto"].dt.date >= date_range[0]) & (df["Fecha de ultimo contacto"].dt.date <= date_range[1])

    df_selection = df.loc[mask]

    # --- KPIs PRINCIPALES ---
    k1, k2, k3 = st.columns(3)
    k1.metric("Q1 - NPS Satisfacción Gral.", f"{calcular_nps(df_selection['Q1 - Satisfacción general']):.1f}%")
    k2.metric("Q2 - NPS Recomendación", f"{calcular_nps(df_selection['Q2 - Recomendación - Concesionario']):.1f}%")
    k3.metric("Muestra Filtrada", len(df_selection))

    st.markdown("---")

    # --- SECCIONES ---
    tab1, tab2, tab3, tab4 = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])

    with tab1:
        st.subheader("Calidad del Asesor")
        c1, c2, c3 = st.columns(3)
        c1.metric("Q4 - Cortesía", f"{calcular_nps(df_selection['Q4 - Cortesía y amabilidad']):.1f}%")
        c2.metric("Q5 - Competencia", f"{calcular_nps(df_selection['Q5 - Competencia Vendedor']):.1f}%")
        c3.metric("Q8 - Info Pre-entrega", f"{calcular_nps(df_selection['Q8 - Satisfacción información entre compra y entrega']):.1f}%")

    with tab2:
        ct1, ct2 = st.columns(2)
        with ct1:
            st.plotly_chart(crear_grafico_torta(df_selection, "Q6 - Ofrecimiento Test Drive", "Q6 - Ofrecimiento TD"), use_container_width=True)
        with ct2:
            st.metric("Q7 - NPS Test Drive", f"{calcular_nps(df_selection['Q7 - Satisfacción Test Drive']):.1f}%")

    with tab3:
        cf1, cf2 = st.columns(2)
        with cf1:
            st.plotly_chart(crear_grafico_torta(df_selection, "Q9 - Financiación utilizada", "Q9 - Tipo de Pago"), use_container_width=True)
        with cf2:
            st.metric("Q10 - NPS Financiación", f"{calcular_nps(df_selection['Q10 - Satisfacción Financiación utilizada']):.1f}%")

    with tab4:
        st.subheader("Finalización del Proceso")
        ce1, ce2 = st.columns(2)
        ce1.metric("Q11 - Momento Entrega", f"{calcular_nps(df_selection['Q11 - Satisfacción Momento de la entrega']):.1f}%")
        ce2.metric("Q13 - Entrega General", f"{calcular_nps(df_selection['Q13 - Satisfacción Entrega General']):.1f}%")
        
        st.markdown("---")
        ce3, ce4 = st.columns(2)
        with ce3:
            st.plotly_chart(crear_grafico_torta(df_selection, "Q14 - Contactado", "Q14 - Contacto Post-Entrega"), use_container_width=True)
        with ce4:
            st.metric("Q15 - NPS Calidad Contacto", f"{calcular_nps(df_selection['Q15 - Satisfacción con el Contacto']):.1f}%")

    st.markdown("---")
    st.subheader("💬 Detalle de Verbalizaciones (Q3)")
    # Formateamos la fecha para que se vea bien en la tabla
    df_display = df_selection[["Fecha de ultimo contacto", "Nombre de cliente", "VIN", "Q3 - Verbalización", "Vendedor"]].copy()
    df_display["Fecha de ultimo contacto"] = df_display["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
    
    st.dataframe(df_display.sort_values(by="Fecha de ultimo contacto", ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
