import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# 1. ID DE TU DOCUMENTO
ID_DOC = "1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNto"

# 2. DICCIONARIO DE HOJAS (Comas corregidas para evitar SyntaxError)
HOJAS = {
    "Enc. Interna CONTAC": "1131519764",
    "TASA DE EMAIL Y RESP": "877908159",
    "Enc Roar": "567460007",
    "VN ROAR": "0"
}

# Selector en la barra lateral
st.sidebar.header("Configuración")
seleccion = st.sidebar.selectbox("Selecciona la hoja a visualizar", list(HOJAS.keys()))

@st.cache_data(ttl=600)
def load_data(gid):
    # Construimos la URL de exportación directa a CSV para esa pestaña específica
    url = f"https://docs.google.com/spreadsheets/d/{ID_DOC}/export?format=csv&gid={gid}"
    # Ignoramos líneas con errores para evitar que el portal se rompa por formato
    return pd.read_csv(url, on_bad_lines='skip', dtype=str)

try:
    df = load_data(HOJAS[seleccion])
    st.subheader(f"Hoja: {seleccion}")
    
    # Buscador opcional
    busqueda = st.text_input(f"Buscar en {seleccion}...")
    if busqueda:
        # Lógica de búsqueda flexible en todas las columnas
        mask = df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df = df[mask]
    
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la hoja {seleccion}")
    st.info("Asegúrate de que el documento esté 'Publicado en la Web' y los GIDs sean correctos.")
