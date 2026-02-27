import streamlit as st
import pandas as pd

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero de Indicadores", layout="wide")
st.title("📊 Tablero de Indicadores: Marca vs Interno")

# 1. TU ENLACE DE PUBLICACIÓN (Mantenlo tal cual lo tienes)
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQBTifZuxjKR35zQencq2bgSWLVMSVir_OkQF1jwTumpJBwSwmxB865sllzXre5b1RFkyn1pVQhE2lf/pub?output=csv"

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
    return pd.read_csv(url_final, on_bad_lines='skip', dtype=str)

# --- FUNCIONES DE CÁLCULO ---
def obtener_metrica(serie):
    # Intentar convertir a número para ver si es escala NPS
    numericos = pd.to_numeric(serie, errors='coerce').dropna()
    
    if not numericos.empty and numericos.max() <= 10:
        # Lógica NPS
        total = len(numericos)
        promotores = len(numericos[numericos >= 9])
        detractores = len(numericos[numericos <= 6])
        nps = ((promotores - detractores) / total) * 100
        return f"{int(nps)}", "NPS"
    
    # Lógica SÍ/NO
    texto = serie.str.strip().str.upper().dropna()
    texto = texto[texto.isin(["SI", "SÍ", "NO"])]
    if not texto.empty:
        total = len(texto)
        si = len(texto[texto.isin(["SI", "SÍ"])])
        porcentaje = (si / total) * 100
        return f"{int(porcentaje)}%", "Cumplimiento"
    
    return None, None

# --- EJECUCIÓN ---
try:
    df = load_data(HOJAS[seleccion])
    
    if seleccion == "Enc Roar":
        st.subheader("🎯 Indicadores de Medición (Columnas Q)")
        # Filtrar columnas que empiezan con Q y no son comentarios largos
        cols_q = [c for c in df.columns if c.startswith('Q') and df[c].str.len().mean() < 20]
        
        if cols_q:
            kpis = st.columns(len(cols_q[:6])) # Mostramos los primeros 6 para no saturar
            for i, col in enumerate(cols_q[:6]):
                valor, tipo = obtener_metrica(df[col])
                if valor:
                    kpis[i].metric(label=f"{col} ({tipo})", value=valor)
        st.divider()

    st.subheader(f"Datos: {seleccion}")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar datos: {e}")
