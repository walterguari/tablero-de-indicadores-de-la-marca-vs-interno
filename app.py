import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

st.title("📊 Monitor de Calidad Total - Método NPS")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

def load_data(url):
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

def calcular_nps(serie):
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    if serie.empty: return 0
    promotores = (serie >= 9).sum()
    detractores = (serie <= 6).sum()
    total = len(serie)
    return ((promotores - detractores) / total) * 100

# Función para crear gráficos de torta consistentes
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
    
    # --- FILTROS ---
    st.sidebar.header("Filtros de Búsqueda")
    marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
    canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())
    vendedor = st.sidebar.multiselect("Vendedor", options=df["Vendedor"].unique(), default=df["Vendedor"].unique())
    
    df_selection = df[
        (df["MARCA"].isin(marca)) & 
        (df["Canal de Venta"].isin(canal)) & 
        (df["Vendedor"].isin(vendedor))
    ]

    # --- KPIs PRINCIPALES ---
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("NPS Satisfacción General", f"{calcular_nps(df_selection['Q1 - Satisfacción general']):.1f}%")
    kpi2.metric("NPS Recomendación", f"{calcular_nps(df_selection['Q2 - Recomendación - Concesionario']):.1f}%")
    kpi3.metric("Total Encuestas", len(df_selection))

    st.markdown("---")

    # --- SECCIONES CON GRÁFICOS DE TORTA ---
    tab1, tab2, tab3, tab4 = st.tabs(["🤝 Proceso de Venta", "🚗 Test Drive", "💰 Financiación", "📦 Entrega y Seguimiento"])

    with tab1:
        st.subheader("Calidad en el Salón")
        c1, c2, c3 = st.columns(3)
        c1.metric("Cortesía y Amabilidad", f"{calcular_nps(df_selection['Q4 - Cortesía y amabilidad']):.1f}%")
        c2.metric("Competencia Vendedor", f"{calcular_nps(df_selection['Q5 - Competencia Vendedor']):.1f}%")
        c3.metric("Inf. Compra/Entrega", f"{calcular_nps(df_selection['Q8 - Satisfacción información entre compra y entrega']):.1f}%")

    with tab2:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.plotly_chart(crear_grafico_torta(df_selection, "Q6 - Ofrecimiento Test Drive", "Q6 - ¿Se ofreció Test Drive?"), use_container_width=True)
        with col_t2:
            st.metric("NPS Satisfacción Test Drive", f"{calcular_nps(df_selection['Q7 - Satisfacción Test Drive']):.1f}%")

    with tab3:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.plotly_chart(crear_grafico_torta(df_selection, "Q9 - Financiación utilizada", "Q9 - Mix de Financiación"), use_container_width=True)
        with col_f2:
            st.metric("NPS Satisfacción Financiación", f"{calcular_nps(df_selection['Q10 - Satisfacción Financiación utilizada']):.1f}%")

    with tab4:
        st.subheader("Entrega y Post-Contacto")
        e1, e2 = st.columns(2)
        e1.metric("NPS Momento Entrega", f"{calcular_nps(df_selection['Q11 - Satisfacción Momento de la entrega']):.1f}%")
        e2.metric("NPS Entrega General", f"{calcular_nps(df_selection['Q13 - Satisfacción Entrega General']):.1f}%")
        
        st.markdown("---")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.plotly_chart(crear_grafico_torta(df_selection, "Q14 - Contactado", "Q14 - ¿Fue contactado post-entrega?"), use_container_width=True)
        with col_e2:
            st.metric("NPS Satisfacción con Contacto", f"{calcular_nps(df_selection['Q15 - Satisfacción con el Contacto']):.1f}%")

    st.markdown("---")
    st.subheader("💬 Verbalizaciones y Detalle")
    st.dataframe(df_selection[["Fecha de ultimo contacto", "Nombre de cliente", "VIN", "Q3 - Verbalización", "Vendedor"]].sort_values(by="Fecha de ultimo contacto", ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
