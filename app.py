import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portal Enc Roar", layout="wide")

# El nuevo enlace que apunta solo a la pestaña Enc Roar
SHEET_URL = "EL_NUEVO_ENLACE_QUE_COPIASTE_AQUI"

@st.cache_data
def load_data():
    # Usamos error_bad_lines=False por si hay filas con formatos extraños en esa hoja
    df = pd.read_csv(SHEET_URL, on_bad_lines='skip')
    return df

st.title("📊 Visualizador: Enc Roar")

try:
    df = load_data()
    
    # Buscador rápido
    busqueda = st.text_input("Buscar en los registros de Enc Roar")
    if busqueda:
        df = df[df.astype(str).apply(lambda x: busqueda.lower() in x.str.lower().values, axis=1)]
    
    st.dataframe(df, use_container_width=True)
    
except Exception as e:
    st.error(f"No se pudo cargar la hoja 'Enc Roar'. Verifica la publicación en la web.")
