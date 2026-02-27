import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tablero de Indicadores", layout="wide")

st.title("📊 Tablero de Indicadores: Marca vs Interno")

# URL de tu Google Sheet publicada como CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit?gid=567460007#gid=567460007"

def load_data():
    return pd.read_csv(SHEET_URL)

try:
    df = load_data()
    st.success("Datos cargados correctamente")
    
    # Filtros rápidos
    marca = st.sidebar.multiselect("Filtrar por Marca", options=df["MARCA"].unique())
    
    if marca:
        df = df[df["MARCA"].isin(marca)]

    st.dataframe(df)
    
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.info("Asegúrate de haber publicado tu Google Sheet como CSV.")
