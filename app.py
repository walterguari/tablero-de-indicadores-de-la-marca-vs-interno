import streamlit as st
import pandas as pd
import numpy as np

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# 2. ENLACE DE PUBLICACIÓN BASE (Copiado de tu imagen de Sheets)
URL_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBTifZuxjKR35zQencq2bgSWLVMSVir_OkQF1jwTumpJBwSwmxB865sllzXre5b1RFkyn1pVQhE2lf/pub?output=csv"

# DICCIONARIO DE HOJAS (Comas corregidas para evitar SyntaxError)
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
    # Construcción dinámica del enlace para cada pestaña
    url_final = f"{URL_BASE}&gid={gid}"
    return pd.read_csv(url_final, on_bad_lines='skip', dtype=str)

# --- FUNCIONES DE CÁLCULO DE INDICADORES ---
def calcular_nps(serie):
    valores = pd.to_numeric(serie, errors='coerce').dropna()
    if valores.empty: return None
    total = len(valores)
    promotores = len(valores[valores >= 9])
    detractores = len(valores[valores <= 6])
    return round(((promotores - detractores) / total) * 100, 1)

def calcular_cumplimiento(serie):
    valores = serie.str.strip().str.upper().dropna()
    validos = valores[valores.isin(["SI", "SÍ", "NO"])]
    if validos.empty: return None
    total = len(validos)
    positivos = len(validos[validos.isin(["SI", "SÍ"])])
    return round((positivos / total) * 100, 1)

# --- EJECUCIÓN ---
try:
    df = load_data(HOJAS[seleccion])
    
    # Procesamiento especial para Enc Roar (Columnas Q)
    if seleccion == "Enc Roar":
        st.subheader("📈 Métricas de Evaluación (Preguntas Q)")
        cols_q = [c for c in df.columns if str(c).upper().startswith('Q')]
        
        if cols_q:
            # Mostramos hasta 5 métricas por fila
            metrica_cols = st.columns(min(len(cols_q), 5))
            for idx, col_name in enumerate(cols_q):
                with metrica_cols[idx % 5]:
                    # Intentamos detectar si es NPS (escala numérica) o SI/NO
                    es_numerico = pd.to_numeric(df[col_name], errors='coerce').dropna()
                    
                    if not es_numerico.empty and es_numerico.max() <= 10:
                        valor_nps = calcular_nps(df[col_name])
                        st.metric(label=f"{col_name} (NPS)", value=valor_nps)
                    else:
                        valor_perc = calcular_cumplimiento(df[col_name])
                        if valor_perc is not None:
                            st.metric(label=f"{col_name} (% SÍ)", value=f"{valor_perc}%")
        st.divider()

    st.subheader(f"Datos: {seleccion}")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.info("Asegúrate de que el documento esté 'Publicado en la Web' como CSV y los GIDs sean correctos.")
