import streamlit as st
import pandas as pd
import plotly.express as px
import math

st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

def load_data(url):
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    df = pd.read_csv(csv_url)
    df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
    return df

def calcular_nps_detallado(serie):
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    total = len(serie)
    if total == 0: return 0, 0, 0, 0
    promotores = (serie >= 9).sum()
    detractores = (serie <= 6).sum()
    nps = ((promotores - detractores) / total) * 100
    return nps, promotores, detractores, total

# Función para calcular cuántas encuestas excelentes faltan para llegar al 94%
def calcular_faltante_94(promotores, detractores, total):
    objetivo = 94
    nps_actual = ((promotores - detractores) / total) * 100
    if nps_actual >= objetivo:
        return "✅ ¡Excelente! Seguir así mejorando y animando."
    
    # Ecuación: ((P + X) - D) / (T + X) = 0.94
    # Despejando X: X = (0.94 * T + D - P) / (1 - 0.94)
    x = (0.94 * total + detractores - promotores) / (1 - 0.94)
    necesarios = math.ceil(x)
    return f"🚨 Faltan {necesarios} encuestas (9-10) para el 94%"

def obtener_color_rango(valor):
    if valor >= 94: return '#28a745'
    if valor >= 90: return '#ffc107'
    return '#dc3545'

def kpi_card(titulo, valor):
    color = obtener_color_rango(valor)
    texto_color = "black" if color == '#ffc107' else "white"
    st.markdown(f"""
        <div style="background-color:{color}; padding:20px; border-radius:10px; text-align:center; border: 1px solid #ddd;">
            <p style="color:{texto_color}; font-size:16px; margin:0;">{titulo}</p>
            <h1 style="color:{texto_color}; margin:0; font-size:45px;">{valor:.1f}%</h1>
        </div>
        """, unsafe_allow_html=True)

try:
    df = load_data(sheet_url)
    
    # --- FILTROS ---
    st.sidebar.header("Filtros Globales")
    df['Anio'] = df["Fecha de ultimo contacto"].dt.year
    df['Mes_Num'] = df["Fecha de ultimo contacto"].dt.month
    
    lista_anios = sorted(df['Anio'].dropna().unique().astype(int), reverse=True)
    anio_sel = st.sidebar.selectbox("Seleccione Año", options=lista_anios)
    
    meses_nombre = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    meses_disponibles = sorted(df[df['Anio'] == anio_sel]['Mes_Num'].unique())
    opciones_meses = [meses_nombre[m] for m in meses_disponibles]
    mes_sel_nombre = st.sidebar.selectbox("Seleccione Mes", options=opciones_meses)
    mes_sel_num = [k for k, v in meses_nombre.items() if v == mes_sel_nombre][0]

    df_base = df[(df["Anio"] == anio_sel) & (df["Mes_Num"] == mes_sel_num)]

    st.title("📊 Gestión de Calidad - Grupo Cenoa")
    p1, p2 = st.tabs(["🏠 Monitor Global", "👤 Rendimiento por Vendedor"])

    with p1:
        nps_q1, _, _, count = calcular_nps_detallado(df_base['Q1 - Satisfacción general'])
        nps_q2, _, _, _ = calcular_nps_detallado(df_base['Q2 - Recomendación - Concesionario'])
        
        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Q1 - NPS Satisfacción", nps_q1)
        with c2: kpi_card("Q2 - NPS Recomendación", nps_q2)
        with c3: st.metric("Encuestas Totales", count)

    with p2:
        st.header("Análisis de Objetivos Stellantis (Mínimo 94%)")
        
        # Procesar datos por vendedor
        resumen = []
        for vend, data in df_base.groupby("Vendedor"):
            nps, prom, detr, total = calcular_nps_detallado(data["Q1 - Satisfacción general"])
            accion = calcular_faltante_94(prom, detr, total)
            resumen.append({"Vendedor": vend, "NPS Q1 %": nps, "Cantidad": total, "Acción/Objetivo": accion})
        
        comp = pd.DataFrame(resumen).sort_values("NPS Q1 %", ascending=False)

        # Gráfico con línea de objetivo
        fig = px.bar(comp, x="Vendedor", y="NPS Q1 %", text="NPS Q1 %",
                     color="NPS Q1 %", range_y=[0, 110],
                     color_continuous_scale=[[0, '#dc3545'], [0.89, '#dc3545'], [0.90, '#ffc107'], [0.939, '#ffc107'], [0.94, '#28a745'], [1, '#28a745']])
        
        # Agregar línea roja de objetivo 94%
        fig.add_hline(y=94, line_dash="dash", line_color="red", annotation_text="Objetivo 94%", annotation_position="top left")
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Tabla de Acción Inmediata")
        
        # Estilo para la tabla: Texto en rojo para los que no llegan
        def color_rojo_fallo(val):
            color = 'red' if '🚨' in str(val) else 'green'
            return f'color: {color}; font-weight: bold'

        st.dataframe(comp.style.applymap(color_rojo_fallo, subset=['Acción/Objetivo']), 
                     use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
