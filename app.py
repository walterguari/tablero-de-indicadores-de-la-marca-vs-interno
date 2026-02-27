import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# PEGA AQUÍ EL ENLACE QUE COPIASTE
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBTiFzuxjKR35zQencq2bgSWLVMSVir_0kQF1jwTumpJBwSwmxB865sllzXre5b1RFkyn1pVQhE2If/pub?output=csv"

# DICCIONARIO DE HOJAS (Revisa que cada línea tenga su coma al final)
HOJAS = {
    "Enc. Interna CONTAC": "1131519764",
    "TASA DE EMAIL Y RESP": "877908159",
    "Enc Roar": "567460007",
    "VN ROAR": "0"
}

st.sidebar.header("Configuración")
seleccion = st.sidebar.selectbox("Selecciona la hoja", list(HOJAS.keys()))

@st.cache_data(ttl=600)
def load_data(gid):
    # Esta fórmula une tu enlace de publicación con la hoja elegida
    url_final = f"{URL_PUB}&gid={gid}"
    return pd.read_csv(url_final, on_bad_lines='skip', dtype=str)

try:
    df = load_data(HOJAS[seleccion])
    st.subheader(f"Datos: {seleccion}")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
