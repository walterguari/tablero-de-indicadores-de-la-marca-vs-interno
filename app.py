import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# 2. ENLACE DE PUBLICACIÓN
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBTifZuxjKR35zQencq2bgSWLVMSVir_OkQF1jwTumpJBwSwmxB865sllzXre5b1RFkyn1pVQhE2lf/pub?output=csv"

# DICCIONARIO DE HOJAS
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
    url_final = f"{URL_PUB}&gid={gid}"
    # Leemos todo como texto inicialmente para evitar errores de tipo
    return pd.read_csv(url_final, on_bad_lines='skip', dtype=str)

def calcular_nps(serie):
    # Convertimos a numérico, ignorando errores (se vuelven NaN)
    valores = pd.to_numeric(serie, errors='coerce').dropna()
    if valores.empty: return None
    
    total = len(valores)
    promotores = len(valores[valores >= 9])
    detractores = len(valores[valores <= 6])
    
    nps = ((promotores - detractores) / total) * 100
    return round(nps, 1)

def calcular_si_no(serie):
    # Limpiamos espacios y pasamos a mayúsculas
    valores = serie.str.strip().str.upper().dropna()
    valores = valores[valores != ""]
    if valores.empty: return None
    
    total = len(valores)
    conteo_si = len(valores[valores == "SI"])
    porcentaje_si = (conteo_si / total) * 100
    return round(porcentaje_si, 1)

try:
    df = load_data(HOJAS[seleccion])
    
    # --- SECCIÓN DE INDICADORES (Solo para Enc Roar) ---
    if seleccion == "Enc Roar":
        st.subheader("📈 Indicadores Clave de Medición")
        
        # Buscamos columnas que empiezan con Q
        columnas_q = [c for c in df.columns if c.upper().startswith('Q')]
        
        if columnas_q:
            # Creamos columnas en Streamlit para mostrar los KPIs en fila
            cols_indicadores = st.columns(len(columnas_q))
            
            for idx, col_name in enumerate(columnas_q):
                # Intentamos detectar si es numérica o texto
                sample = pd.to_numeric(df[col_name], errors='coerce').dropna()
                
                with cols_indicadores[idx % len(cols_indicadores)]:
                    if not sample.empty and sample.max() <= 10:
                        # Es una columna de escala 1-10 -> Calcular NPS
                        nps_val = calcular_nps(df[col_name])
                        st.metric(label=f"NPS {col_name}", value=f"{nps_val}", delta="Objetivo: >70")
                    else:
                        # Es una columna de texto -> Calcular % de "SI"
                        perc_si = calcular_si_no(df[col_name])
                        if perc_si is not None:
                            st.metric(label=f"% SI {col_name}", value=f"{perc_si}%")
        st.markdown("---")

    st.subheader(f"Datos: {seleccion}")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
