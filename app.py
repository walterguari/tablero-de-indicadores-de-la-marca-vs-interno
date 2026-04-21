import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

# --- FUNCIONES DE DATOS Y CÁLCULOS ---
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

def calcular_faltante_94(promotores, detractores, total):
    objetivo = 94
    nps_actual = ((promotores - detractores) / total) * 100
    if nps_actual >= objetivo:
        return "✅ ¡Excelente! Seguir así mejorando y animando."
    # Ecuación para llegar al 94% de NPS
    x = (0.94 * total + detractores - promotores) / (1 - 0.94)
    necesarios = math.ceil(x)
    return f"🚨 Faltan {necesarios} encuestas (9-10) para el 94%"

# --- FUNCIONES VISUALES ---
def crear_gauge_nps(valor, titulo):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': titulo, 'font': {'size': 20, 'color': '#333', 'weight': 'bold'}},
        number = {'suffix': "%", 'font': {'size': 50, 'color': '#333'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#333"}, 
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#eee",
            'steps': [
                {'range': [0, 89.9], 'color': '#dc3545'},    # Rojo
                {'range': [90, 93.9], 'color': '#ffc107'},   # Amarillo
                {'range': [94, 100], 'color': '#28a745'}     # Verde
            ],
            'threshold': {
                'line': {'color': "black", 'width': 5},
                'thickness': 0.8,
                'value': 94
            }
        }
    ))
    fig.update_layout(height=350, margin=dict(l=30, r=30, t=50, b=20))
    return fig

def crear_grafico_torta(df, columna, titulo):
    conteo = df[columna].value_counts().reset_index()
    conteo.columns = [columna, 'Cantidad']
    fig = px.pie(conteo, values='Cantidad', names=columna, title=titulo, hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label+value')
    return fig

# --- EJECUCIÓN PRINCIPAL ---
try:
    df = load_data(sheet_url)
    
    # --- FILTROS LATERALES ---
    st.sidebar.header("Filtros Globales")
    df['Anio'] = df["Fecha de ultimo contacto"].dt.year
    df['Mes_Num'] = df["Fecha de ultimo contacto"].dt.month
    
    lista_anios = sorted(df['Anio'].dropna().unique().astype(int), reverse=True)
    anio_sel = st.sidebar.selectbox("Seleccione Año", options=lista_anios)
    
    meses_nombre = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    meses_disponibles = sorted(df[df['Anio'] == anio_sel]['Mes_Num'].unique())
    mes_sel_nombre = st.sidebar.selectbox("Seleccione Mes", options=[meses_nombre[m] for m in meses_disponibles])
    mes_sel_num = [k for k, v in meses_nombre.items() if v == mes_sel_nombre][0]

    marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
    canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())

    # Data base filtrada
    df_base = df[(df["Anio"] == anio_sel) & (df["Mes_Num"] == mes_sel_num) & 
                 (df["MARCA"].isin(marca)) & (df["Canal de Venta"].isin(canal))]

    st.title("📊 Gestión de Calidad - Grupo Cenoa")
    p1, p2 = st.tabs(["🏠 Monitor Global", "👤 Rendimiento por Vendedor"])

    # --- PESTAÑA 1: MONITOR GLOBAL ---
    with p1:
        st.header(f"Resultados Globales - {mes_sel_nombre} {anio_sel}")
        nps_q1, _, _, total_mue = calcular_nps_detallado(df_base['Q1 - Satisfacción general'])
        nps_q2, _, _, _ = calcular_nps_detallado(df_base['Q2 - Recomendación - Concesionario'])
        
        # Gráficos tipo RELOJ
        c_rel1, c_rel2, c_rel3 = st.columns([2, 2, 1])
        with c_rel1:
            st.plotly_chart(crear_gauge_nps(nps_q1, "Q1 - SATISFACCIÓN"), use_container_width=True)
        with c_rel2:
            st.plotly_chart(crear_gauge_nps(nps_q2, "Q2 - RECOMENDACIÓN"), use_container_width=True)
        with c_rel3:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.metric("Encuestas Totales", total_mue)

        st.markdown("<br>", unsafe_allow_html=True)
        sub1, sub2, sub3, sub4 = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
        
        with sub1:
            v1, v2, v3 = st.columns(3)
            v1.metric("Q4 - Cortesía", f"{calcular_nps_detallado(df_base['Q4 - Cortesía y amabilidad'])[0]:.1f}%")
            v2.metric("Q5 - Competencia", f"{calcular_nps_detallado(df_base['Q5 - Competencia Vendedor'])[0]:.1f}%")
            v3.metric("Q8 - Info Pre-entrega", f"{calcular_nps_detallado(df_base['Q8 - Satisfacción información entre compra y entrega'])[0]:.1f}%")
        with sub2:
            ct1, ct2 = st.columns(2)
            with ct1: st.plotly_chart(crear_grafico_torta(df_base, "Q6 - Ofrecimiento Test Drive", "Q6 - Ofrecimiento TD"), use_container_width=True)
            with ct2: st.metric("Q7 - NPS Test Drive", f"{calcular_nps_detallado(df_base['Q7 - Satisfacción Test Drive'])[0]:.1f}%")
        with sub3:
            cf1, cf2 = st.columns(2)
            with cf1: st.plotly_chart(crear_grafico_torta(df_base, "Q9 - Financiación utilizada", "Q9 - Tipo de Pago"), use_container_width=True)
            with cf2: st.metric("Q10 - NPS Financiación", f"{calcular_nps_detallado(df_base['Q10 - Satisfacción Financiación utilizada'])[0]:.1f}%")
        with sub4:
            ce1, ce2 = st.columns(2)
            ce1.metric("Q11 - Momento Entrega", f"{calcular_nps_detallado(df_base['Q11 - Satisfacción Momento de la entrega'])[0]:.1f}%")
            ce2.metric("Q13 - Entrega General", f"{calcular_nps_detallado(df_base['Q13 - Satisfacción Entrega General'])[0]:.1f}%")

        st.markdown("---")
        st.subheader("💬 Comentarios y Verbalizaciones (Q3)")
        if not df_base.empty:
            df_verbal = df_base[["Fecha de ultimo contacto", "Nombre de cliente", "Q3 - Verbalización", "Vendedor"]].copy()
            df_verbal["Fecha de ultimo contacto"] = df_verbal["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_verbal.sort_values("Fecha de ultimo contacto", ascending=False), use_container_width=True, hide_index=True)

    # --- PESTAÑA 2: RENDIMIENTO POR VENDEDOR ---
    with p2:
        st.header("Análisis de Objetivos Stellantis (Mínimo 94%)")
        if not df_base.empty:
            resumen = []
            for vend, data in df_base.groupby("Vendedor"):
                nps_v, prom_v, detr_v, total_v = calcular_nps_detallado(data["Q1 - Satisfacción general"])
                accion = calcular_faltante_94(prom_v, detr_v, total_v)
                resumen.append({"Vendedor": vend, "NPS Q1 %": nps_v, "Cantidad": total_v, "Acción/Objetivo": accion})
            
            comp = pd.DataFrame(resumen).sort_values("NPS Q1 %", ascending=False)
            
            # Ranking de barras
            fig_rank = px.bar(comp, x="Vendedor", y="NPS Q1 %", text="NPS Q1 %", color="NPS Q1 %", range_y=[0, 110],
                              color_continuous_scale=[[0, '#dc3545'], [0.899, '#dc3545'], [0.90, '#ffc107'], [0.939, '#ffc107'], [0.94, '#28a745'], [1, '#28a745']])
            fig_rank.add_hline(y=94, line_dash="dash", line_color="black", annotation_text="Objetivo 94%")
            fig_rank.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            st.plotly_chart(fig_rank, use_container_width=True)

            st.subheader("Tabla de Acción Inmediata")
            def color_rojo_fallo(val):
                color = 'red' if '🚨' in str(val) else 'green'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(comp[["Vendedor", "NPS Q1 %", "Cantidad", "Acción/Objetivo"]].style.map(color_rojo_fallo, subset=['Acción/Objetivo']), 
                         use_container_width=True, hide_index=True)
        else:
            st.warning("No hay datos para mostrar.")

except Exception as e:
    st.error(f"Error crítico: {e}")
