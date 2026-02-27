import streamlit as st
import pandas as pd

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# 1. ENLACE DE PUBLICACIÓN (ID del documento publicado como CSV)
# Usamos el ID que aparece en tu ventana de 'Publicar en la Web'
ID_PUB = "2PACX-1vQBTifZuxjKR35zQencq2bgSWLVMSVir_OkQF1jwTumpJBwSwmxB865sllzXre5b1RFkyn1pVQhE2lf"

# 2. DICCIONARIO DE HOJAS (Comas corregidas)
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
    # Construimos la URL de exportación directa usando el ID de publicación
    url = f"https://docs.google.com/spreadsheets/d/e/{ID_PUB}/pub?output=csv&gid={gid}"
    # on_bad_lines='skip' evita errores si hay filas con formatos extraños
    return pd.read_csv(url, on_bad_lines='skip', dtype=str)

try:
    df = load_data(HOJAS[seleccion])
    st.subheader(f"Hoja: {seleccion}")
    
    # Buscador rápido
    busqueda = st.text_input(f"Buscar en {seleccion}...")
    if busqueda:
        mask = df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
        df = df[mask]
    
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la hoja {seleccion}")
    st.info("Asegúrate de que el documento esté 'Publicado en la Web' y los GIDs sean correctos.")
