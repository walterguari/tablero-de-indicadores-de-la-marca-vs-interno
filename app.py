import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

# Título del Portal
st.title("📊 Monitor de Calidad y NPS - Enc Roar")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

def load_data(url):
    # El gid 567460007 corresponde a la hoja "Enc Roar"
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

# Función para calcular NPS
def calcular_nps(serie):
    if serie.empty: return 0
    promotores = (serie >= 9).sum()
    detractores = (serie <= 6).sum()
    total = len(serie)
    if total == 0: return 0
    return ((promotores - detractores) / total) * 100

try:
    df = load_data(sheet_url)
    
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Búsqueda")
    
    marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
    canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())
    vendedor = st.sidebar.multiselect("Vendedor", options=df["Vendedor"].unique(), default=df["Vendedor"].unique())
    
    # Filtrar datos
    df_selection = df[
        (df["MARCA"].isin(marca)) & 
        (df["Canal de Venta"].isin(canal)) & 
        (df["Vendedor"].isin(vendedor))
    ]

    # --- INDICADORES NPS (Métricas) ---
    st.subheader("Indicadores de Lealtad (NPS)")
    nps_q1 = calcular_nps(df_selection["Q1 - Satisfacción general"])
    nps_q2 = calcular_nps(df_selection["Q2 - Recomendación - Concesionario"])
    
    m1, m2, m3 = st.columns(3)
    # Mostramos el NPS con un color dinámico
    m1.metric("NPS Q1 (Satisfacción)", f"{nps_q1:.1f}%")
    m2.metric("NPS Q2 (Recomendación)", f"{nps_q2:.1f}%")
    m3.metric("Total Encuestas", len(df_selection))

    st.markdown("---")

    # --- DETALLE DE CLIENTES Y OBSERVACIONES ---
    st.subheader("Detalle de Contactos y Verbalizaciones")
    
    columnas_detalle = [
        "Fecha de ultimo contacto", 
        "Nombre de cliente", 
        "VIN", 
        "Q3 - Verbalización",
        "Vendedor"
    ]
    
    st.dataframe(
        df_selection[columnas_detalle].sort_values(by="Fecha de ultimo contacto", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # --- GRÁFICO DE VENDEDORES ---
    st.subheader("Performance por Vendedor (Cant. Encuestas)")
    
    conteo_vendedores = df_selection["Vendedor"].value_counts().reset_index()
    conteo_vendedores.columns = ['Vendedor', 'Encuestas']
    
    fig_vendedor = px.bar(
        conteo_vendedores,
        x='Vendedor',
        y='Encuestas',
        color='Vendedor',
        text='Encuestas',
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    
    fig_vendedor.update_traces(textposition='outside')
    st.plotly_chart(fig_vendedor, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos o nombres de columnas: {e}")
    st.info("Revisa que los nombres de las columnas en Google Sheets no hayan cambiado.")
