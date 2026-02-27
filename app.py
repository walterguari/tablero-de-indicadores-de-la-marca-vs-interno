import streamlit as st
import pandas as pd

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# 2. ENLACE DE PUBLICACIÓN CORREGIDO
# Basado en tu imagen de 'Publicar en la web', este es el enlace base:
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBTifZuxjKR35zQencq2bgSWLVMSVir_OkQF1jwTumpJBwSwmxB865sllzXre5b1RFkyn1pVQhE2lf/pub?output=csv"

# DICCIONARIO DE HOJAS CON GIDs CORRECTOS
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
    # Combinamos la URL base con el ID de la hoja específica
    url_final = f"{URL_BASE}&gid={gid}"
    # on_bad_lines='skip' evita el error de la línea 84 que tuviste antes
    return pd.read_csv(url_final, on_bad_lines='skip', dtype=str)

# --- FUNCIONES PARA INDICADORES ---
def calcular_metricas_q(df):
    # Filtrar columnas que empiezan con Q
    cols_q = [c for c in df.columns if str(c).upper().startswith('Q')]
    
    if not cols_q:
        return
        
    st.subheader("📈 Indicadores de Medición (Enc Roar)")
    # Mostramos los indicadores en columnas
    columnas_web = st.columns(min(len(cols_q), 5))
    
    for i, col in enumerate(cols_q):
        datos = df[col].dropna()
        if datos.empty:
            continue
            
        # Intentar detectar si es numérico (Escala 1-10)
        numericos = pd.to_numeric(datos, errors='coerce').dropna()
        
        with columnas_web[i % 5]:
            if not numericos.empty and numericos.max() <= 10:
                # CÁLCULO NPS: (Promotores - Detractores) / Total * 100
                total = len(numericos)
                prom = len(numericos[numericos >= 9])
                det = len(numericos[numericos <= 6])
                nps = ((prom - det) / total) * 100
                st.metric(label=f"{col} (NPS)", value=f"{int(nps)}")
            else:
                # CÁLCULO CUMPLIMIENTO (% SI)
                texto = datos.str.strip().str.upper()
                si = len(texto[texto.isin(['SI', 'SÍ'])])
                total_resp = len(texto[texto.isin(['SI', 'SÍ', 'NO'])])
                if total_resp > 0:
                    perc = (si / total_resp) * 100
                    st.metric(label=f"{col} (% SÍ)", value=f"{int(perc)}%")

# --- EJECUCIÓN ---
try:
    df = load_data(HOJAS[seleccion])
    
    # Si es Enc Roar, mostramos los indicadores arriba
    if seleccion == "Enc Roar":
        calcular_metricas_q(df)
        st.divider()

    st.subheader(f"Datos: {seleccion}")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.info("Revisa que el enlace de publicación en Google Sheets siga activo.")
