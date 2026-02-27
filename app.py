import streamlit as st
import pandas as pd

# Configuración visual del portal
st.set_page_config(page_title="Portal VN CIEL", layout="wide")
st.title("🚗 Gestión de Unidades - CIEL")
st.markdown("---")

# ENLACE DE DATOS (Asegúrate de que termine en output=csv)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit?gid=567460007#gid=567460007"

@st.cache_data(ttl=600)
def load_data():
    try:
        # Cargamos los datos forzando a texto para no perder ceros a la izquierda en chasis/teléfonos
        df = pd.read_csv(SHEET_URL, dtype=str)
        # Limpiamos nombres de columnas por si tienen espacios ocultos
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

df = load_data()

if df is not None:
    # --- BUSCADOR Y FILTROS ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Filtros")
        # Filtro por Marca (Peugeot, Citroen, etc)
        if 'MARCA' in df.columns:
            marcas = st.multiselect("Seleccionar Marca", options=df['MARCA'].unique())
            if marcas:
                df = df[df['MARCA'].isin(marcas)]
        
        # Filtro por Canal de Venta
        if 'CANAL VENTA' in df.columns:
            canales = st.multiselect("Canal de Venta", options=df['CANAL VENTA'].unique())
            if canales:
                df = df[df['CANAL VENTA'].isin(canales)]

    with col2:
        st.subheader("Buscador Global")
        busqueda = st.text_input("Buscar por Cliente o Chasis...")
        if busqueda:
            # Filtro de búsqueda en todo el DataFrame
            df = df[df.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)]

    # --- TABLA DE RESULTADOS ---
    st.write(f"Mostrando {len(df)} registros")
    st.dataframe(df, use_container_width=True)
    
    # Botón para descargar reporte
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Vista Actual", data=csv, file_name="reporte_ciel.csv", mime="text/csv")

else:
    st.info("💡 Consejo: Revisa que tu Google Sheet esté 'Publicado en la Web' como CSV.")
