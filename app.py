import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

# Título del Portal
st.title("📊 Monitor de Calidad Total - Método NPS")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

def load_data(url):
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

# Función para calcular NPS (Promotores 9-10, Detractores 0-6)
def calcular_nps(serie):
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    if serie.empty: return 0
    promotores = (serie >= 9).sum()
    detractores = (serie <= 6).sum()
    total = len(serie)
    return ((promotores - detractores) / total) * 100

try:
    df = load_data(sheet_url)
    
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Búsqueda")
    marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
    canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())
    vendedor = st.sidebar.multiselect("Vendedor", options=df["Vendedor"].unique(), default=df["Vendedor"].unique())
    
    df_selection = df[
        (df["MARCA"].isin(marca)) & 
        (df["Canal de Venta"].isin(canal)) & 
        (df["Vendedor"].isin(vendedor))
    ]

    # --- INDICADORES PRINCIPALES (KPIs) ---
    st.header("🏆 Indicadores Clave de Lealtad")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("NPS Satisfacción General", f"{calcular_nps(df_selection['Q1 - Satisfacción general']):.1f}%")
    kpi2.metric("NPS Recomendación", f"{calcular_nps(df_selection['Q2 - Recomendación - Concesionario']):.1f}%")
    kpi3.metric("Total Encuestas", len(df_selection))

    st.markdown("---")

    # --- SECCIONES DETALLADAS ---
    tab1, tab2, tab3, tab4 = st.tabs(["🤝 Proceso de Venta", "🚗 Test Drive", "💰 Financiación", "📦 Entrega y Seguimiento"])

    with tab1:
        st.subheader("Calidad en el Salón de Ventas")
        c1, c2, c3 = st.columns(3)
        c1.metric("Cortesía y Amabilidad", f"{calcular_nps(df_selection['Q4 - Cortesía y amabilidad']):.1f}%")
        c2.metric("Competencia Vendedor", f"{calcular_nps(df_selection['Q5 - Competencia Vendedor']):.1f}%")
        c3.metric("Inf. Compra/Entrega", f"{calcular_nps(df_selection['Q8 - Satisfacción información entre compra y entrega']):.1f}%")

    with tab2:
        st.subheader("Experiencia de Manejo")
        t1, t2 = st.columns(2)
        # Para Q6 (Ofrecimiento) mostramos porcentaje de "SI"
        ofrecimiento = (df_selection['Q6 - Ofrecimiento Test Drive'] == 'Sí').mean() * 100
        t1.metric("% Ofrecimiento Test Drive", f"{ofrecimiento:.1f}%")
        t2.metric("NPS Satisfacción Test Drive", f"{calcular_nps(df_selection['Q7 - Satisfacción Test Drive']):.1f}%")

    with tab3:
        st.subheader("Gestión Financiera")
        f1, f2 = st.columns(2)
        f1.metric("NPS Satisfacción Financiación", f"{calcular_nps(df_selection['Q10 - Satisfacción Financiación utilizada']):.1f}%")
        # Mostramos la financiación más usada
        finan_top = df_selection['Q9 - Financiación utilizada'].mode()[0] if not df_selection.empty else "N/A"
        f2.write(f"**Canal Financiero más usado:** {finan_top}")

    with tab4:
        st.subheader("Entrega y Post-Contacto")
        e1, e2, e3 = st.columns(3)
        e1.metric("NPS Momento Entrega", f"{calcular_nps(df_selection['Q11 - Satisfacción Momento de la entrega']):.1f}%")
        e2.metric("NPS Entrega General", f"{calcular_nps(df_selection['Q13 - Satisfacción Entrega General']):.1f}%")
        e3.metric("NPS Calidad de Contacto", f"{calcular_nps(df_selection['Q15 - Satisfacción con el Contacto']):.1f}%")

    st.markdown("---")

    # --- TABLA DE DETALLE ---
    st.subheader("💬 Verbalizaciones y Detalle")
    st.dataframe(
        df_selection[["Fecha de ultimo contacto", "Nombre de cliente", "VIN", "Q3 - Verbalización", "Vendedor"]].sort_values(by="Fecha de ultimo contacto", ascending=False),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"Error: {e}")
