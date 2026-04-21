import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Tablero de Indicadores", layout="wide")

st.title("📊 Datos desde Google Sheets - Enc Roar")

# URL de tu Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

# Función simplificada para leer la hoja específica
def load_data(url):
    # Forzamos la descarga del GID específico en formato CSV
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

try:
    df = load_data(sheet_url)
    st.success("¡Datos cargados correctamente!")
    st.dataframe(df)
except Exception as e:
    st.error(f"Error al conectar: {e}")
