import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# 2. ENLACE DE PUBLICACIÓN BASE (Corregido para evitar el error 404)
# Nota: He quitado el final "output=csv" para agregarlo dinámicamente
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBTifZuxjKR35zQencq2bgSWLVMSVir_OkQF1jwTumpJBwSwmxB865sllzXre5b1RFkyn1pVQhE2lf/pub?"

# 3. DICCIONARIO DE HOJAS (GIDs verificados)
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
    # Construcción robusta de la URL
    url_final = f"{URL_BASE}output=csv&gid={gid}"
    # on_bad_lines='skip' es vital por los errores de formato que vimos antes
    return pd.read_csv(url_final, on_bad_lines='skip', dtype=str)

# --- FUNCIONES DE CÁLCULO DE INDICADORES ---
def mostrar_indicadores(df):
    st.subheader(f"📈 Indicadores de Medición: {seleccion}")
    
    # Buscamos columnas que empiecen con Q (ignora mayúsculas/minúsculas)
    cols_q = [c for c in df.columns if str(c).upper().startswith('Q')]
    
    if cols_q:
        # Creamos una fila de métricas (máximo 5)
        metricas = st.columns(min(len(cols_q), 5))
        
        for i, col in enumerate(cols_q):
            # Limpieza de datos: quitar vacíos
            datos = pd.to_numeric(df[col], errors='coerce').dropna()
            
            with metricas[i % 5]:
                if not datos.empty and datos.max() <= 10:
                    # CÁLCULO NPS
                    total = len(datos)
                    prom = len(datos[datos >= 9])
                    det = len(datos[datos <= 6])
                    nps = int(((prom - det) / total) * 100)
                    st.metric(label=f"{col} (NPS)", value=nps)
                else:
                    # CÁLCULO % SÍ (para textos)
                    texto = df[col].str.strip().str.upper()
                    si = len(texto[texto.isin(['SI', 'SÍ'])])
                    total_resp = len(texto[texto.isin(['SI', 'SÍ', 'NO'])])
                    if total_resp > 0:
                        perc = int((si / total_resp) * 100)
                        st.metric(label=f"{col} (% SÍ)", value=f"{perc}%")

# --- EJECUCIÓN PRINCIPAL ---
try:
    df_datos = load_data(HOJAS[seleccion])
    
    # Si la hoja tiene columnas de preguntas "Q", mostrar indicadores
    if seleccion == "Enc Roar" or seleccion == "Enc. Interna CONTAC":
        mostrar_indicadores(df_datos)
        st.divider()

    st.subheader(f"Vista de Datos: {seleccion}")
    st.dataframe(df_datos, use_container_width=True)

except Exception as e:
    st.error(f"Error al conectar: {e}")
    st.info("Por favor, verifica que el archivo siga 'Publicado en la Web' en Google Sheets.")
