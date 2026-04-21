import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tablero de Calidad - Cenoa", layout="wide")

# Estilo personalizado para el título
st.title("📊 Control de Gestión: Encuestas Roar")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

def load_data(url):
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

try:
    df = load_data(sheet_url)
    
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros")
    
    # Asumimos que existe una columna llamada 'Sucursal' o similar. 
    # Si tiene otro nombre en tu Excel, cámbialo aquí:
    col_sucursal = 'Sucursal' if 'Sucursal' in df.columns else df.columns[0]
    
    sucursales = st.sidebar.multiselect(
        "Seleccione Sucursal:",
        options=df[col_sucursal].unique(),
        default=df[col_sucursal].unique()
    )

    # Filtrar datos
    df_selection = df[df[col_sucursal].isin(sucursales)]

    # --- MÉTRICAS PRINCIPALES ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Encuestas", f"{len(df_selection)}")
    
    with col2:
        # Ejemplo: Promedio de una columna numérica (ajustar nombre según tu hoja)
        st.metric("Cumplimiento", "92%", "+2%") 
        
    with col3:
        st.metric("Pendientes", "5", delta_color="inverse")

    st.markdown("""---""")

    # --- VISUALIZACIÓN ---
    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Distribución por Sucursal")
        fig_sucursal = px.bar(
            df_selection[col_sucursal].value_counts().reset_index(),
            x='index',
            y=col_sucursal,
            labels={'index': 'Sucursal', col_sucursal: 'Cantidad'},
            template="plotly_white",
            color_discrete_sequence=["#0083B8"]
        )
        st.plotly_chart(fig_sucursal, use_container_width=True)

    with right_column:
        st.subheader("Vista Detallada")
        st.dataframe(df_selection, height=300)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
