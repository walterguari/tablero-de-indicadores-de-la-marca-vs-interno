import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Portal VN CIEL", layout="wide")

st.title("📊 Tablero de Control - VN CIEL")
st.markdown("---")

# 1. PEGA AQUÍ TU ENLACE CSV (El que termina en output=csv)
SHEET_URL = "TU_ENLACE_AQUI_DEBE_TERMINAR_EN_output=csv"

@st.cache_data(ttl=600)  # Los datos se actualizan cada 10 minutos
def load_data():
    try:
        # Leemos el CSV y forzamos a que todo sea texto para evitar errores con chasis o teléfonos
        df = pd.read_csv(SHEET_URL, dtype=str)
        # Limpiamos espacios en blanco en los nombres de las columnas
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"No se pudo conectar con la base de datos. Error: {e}")
        return None

df = load_data()

if df is not None:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Búsqueda")
    
    # Buscador de texto global
    search_query = st.sidebar.text_input("Buscar por Cliente o Chasis", "")

    # Filtros por columnas específicas (Marca y Modelo)
    if 'MARCA' in df.columns:
        marcas = st.sidebar.multiselect("Filtrar por Marca", options=df['MARCA'].unique())
        if marcas:
            df = df[df['MARCA'].isin(marcas)]
            
    if 'MODELO' in df.columns:
        modelos = st.sidebar.multiselect("Filtrar por Modelo", options=df['MODELO'].unique())
        if modelos:
            df = df[df['MODELO'].isin(modelos)]

    # --- LÓGICA DE BÚSQUEDA ---
    if search_query:
        # Busca en todas las columnas el texto ingresado
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    # --- VISUALIZACIÓN ---
    st.subheader(f"Resultados: {len(df)} registros encontrados")
    
    # Mostramos la tabla interactiva
    st.dataframe(df, use_container_width=True)

    # Botón para descargar lo que estás viendo
    csv_download = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar esta vista como CSV",
        data=csv_download,
        file_name="reporte_ciel.csv",
        mime="text/csv",
    )
else:
    st.warning("⚠️ Esperando conexión con Google Sheets. Verifica que el archivo esté 'Publicado en la Web' como CSV.")
