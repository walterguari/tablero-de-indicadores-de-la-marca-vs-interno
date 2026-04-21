import streamlit as st
from library.st_gsheets_connection import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Tablero de Indicadores", layout="wide")

st.title("📊 Datos desde Google Sheets - Enc Roar")

# URL de tu Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

# Función para cargar los datos
def load_data(url):
    # Convertimos la URL de edición en una URL de exportación CSV para la hoja específica
    # El gid 567460007 corresponde a "Enc Roar"
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url)

try:
    df = load_data(sheet_url)
    
    # Mostrar un resumen de los datos
    st.success("¡Datos cargados correctamente desde la hoja Enc Roar!")
    
    # Filtro rápido para visualizar
    if st.checkbox("Mostrar tabla de datos crudos"):
        st.dataframe(df)

    # Ejemplo de visualización de métricas si existen columnas de indicadores
    # Aquí puedes personalizar según las columnas reales de tu hoja "Enc Roar"
    st.subheader("Resumen de Indicadores")
    st.write(f"Total de registros encontrados: {len(df)}")

except Exception as e:
    st.error(f"No se pudo conectar con la hoja. Asegúrate de que el archivo sea 'Público' (Cualquier persona con el enlace puede leer).")
    st.info("Error técnico: " + str(e))
