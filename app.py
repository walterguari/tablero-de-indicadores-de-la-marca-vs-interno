import streamlit as st
import pandas as pd

# Configuración de página
st.set_page_config(page_title="Tablero de Indicadores", layout="wide")

st.title("📊 Tablero de Indicadores: Marca vs Interno")

# --- CONFIGURACIÓN DE LAS HOJAS ---
# Debes obtener el ID de tu documento de la URL de Google Sheets
# Ejemplo: https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
SPREADSHEET_ID = "1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNto"

# Diccionario con los nombres de tus hojas y sus respectivos GIDs
# Puedes encontrar el GID al final de la URL cuando seleccionas cada pestaña en Sheets (?gid=XXXX)
HOJAS = {
    "Enc Roar": "567460007",
    "VN ROAR": "ESCRIBE_AQUI_EL_GID_DE_VN_ROAR",
    "TASA DE EMAIL Y RESP": "ESCRIBE_AQUI_EL_GID_DE_ESTA_HOJA"
}

def get_csv_url(sheet_gid):
    return f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={sheet_gid}"

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
seleccion_hoja = st.sidebar.selectbox("Selecciona la hoja a visualizar", list(HOJAS.keys()))

@st.cache_data(ttl=600)
def load_data(gid):
    url = get_csv_url(gid)
    # Usamos on_bad_lines='skip' para evitar el error de tokenización que tuviste antes
    return pd.read_csv(url, on_bad_lines='skip', dtype=str)

try:
    gid_seleccionado = HOJAS[seleccion_hoja]
    df = load_data(gid_seleccionado)
    
    st.subheader(f"Datos de la hoja: {seleccion_hoja}")
    
    # Buscador global
    busqueda = st.text_input("Buscar en esta hoja...")
    if busqueda:
        df = df[df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)]

    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar la hoja {seleccion_hoja}")
    st.info("Asegúrate de que el documento esté 'Publicado en la Web' y los GIDs sean correctos.")
