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
    try:
        csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
        df = pd.read_csv(csv_url)
        df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
        
        # Clasificación para los botones de filtro
        def categorizar(val):
            val = pd.to_numeric(val, errors='coerce')
            if val >= 9: return "Promotor"
            if val >= 7: return "Neutro"
            if val <= 6: return "Detractor"
            return "Sin Datos"
        df['Categoria_NPS'] = df['Q1 - Satisfacción general'].apply(categorizar)
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

def calcular_nps_detallado(serie):
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    total = len(serie)
    if total == 0: return 0, 0, 0, 0, 0
    promotores = (serie >= 9).sum()
    neutros = ((serie >= 7) & (serie <= 8)).sum()
    detractores = (serie <= 6).sum()
    nps = ((promotores - detractores) / total) * 100
    return nps, promotores, neutros, detractores, total

def calcular_faltante_94(promotores, detractores, total):
    if total == 0: return "Sin datos"
    nps_actual = ((promotores - detractores) / total) * 100
    if nps_actual >= 94: return "✅ Objetivo cumplido."
    x = (0.94 * total + detractores - promotores) / (1 - 0.94)
    return f"🚨 Faltan {math.ceil(x)} encuestas (9-10) para el 94%"

# --- DISEÑO DE RELOJ CORREGIDO (SIN PADDING ERROR) ---
def crear_gauge_moderno(valor, titulo):
    color_viva = '#28a745' if valor >= 94 else ('#ffc107' if valor >= 90 else '#dc3545')
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': f"<b>{titulo}</b>", 'font': {'size': 20}},
        number = {'suffix': "%", 'font': {'size': 40}},
        gauge = {
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': 94}
        }
    ))
    fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig

# --- LÓGICA PRINCIPAL ---
try:
    df = load_data(sheet_url)
    if not df.empty:
        # --- BARRA LATERAL ---
        st.sidebar.header("Filtros Globales")
        df['Anio'] = df["Fecha de ultimo contacto"].dt.year
        df['Mes_Num'] = df["Fecha de ultimo contacto"].dt.month
        
        anio_sel = st.sidebar.selectbox("Año", sorted(df['Anio'].dropna().unique().astype(int), reverse=True))
        meses_n = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        meses_disp = sorted(df[df['Anio'] == anio_sel]['Mes_Num'].unique())
        mes_sel = st.sidebar.selectbox("Mes", [meses_n[m] for m in meses_disp])
        mes_num = [k for k, v in meses_n.items() if v == mes_sel][0]

        marcas = st.sidebar.multiselect("MARCA", df["MARCA"].unique(), df["MARCA"].unique())
        df_base = df[(df["Anio"] == anio_sel) & (df["Mes_Num"] == mes_num) & (df["MARCA"].isin(marcas))]

        st.title("📊 Gestión de Calidad - Grupo Cenoa")
        tab_global, tab_vendedores = st.tabs(["🏠 Monitor Global", "👤 Rendimiento por Vendedor"])

        with tab_global:
            st.header(f"Resultados de {mes_sel} {anio_sel}")
            nps_q1, p_q1, n_q1, d_q1, t_q1 = calcular_nps_detallado(df_base['Q1 - Satisfacción general'])
            nps_q2, _, _, _, _ = calcular_nps_detallado(df_base['Q2 - Recomendación - Concesionario'])

            # --- RELOJES ---
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.plotly_chart(crear_gauge_moderno(nps_q1, "Q1 - SATISFACCIÓN"), use_container_width=True)
                st.write("**Filtrar comentarios por:**")
                cb1, cb2, cb3 = st.columns(3)
                # Botones de filtro
                if 'f' not in st.session_state: st.session_state.f = "Todos"
                if cb1.button(f"🟢 {p_q1}\nProm"): st.session_state.f = "Promotor"
                if cb2.button(f"🟡 {n_q1}\nNeu"): st.session_state.f = "Neutro"
                if cb3.button(f"🔴 {d_q1}\nDet"): st.session_state.f = "Detractor"
            with c2:
                st.plotly_chart(crear_gauge_moderno(nps_q2, "Q2 - RECOMENDACIÓN"), use_container_width=True)
            with c3:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.metric("Total Muestra", t_q1)
                if st.button("🔄 Ver Todos"): st.session_state.f = "Todos"

            # --- SUB-TABS INDICADORES ---
            st.markdown("---")
            stabs = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
            with stabs[0]:
                v1, v2, v3 = st.columns(3)
                v1.metric("Q4 - Cortesía", f"{calcular_nps_detallado(df_base['Q4 - Cortesía y amabilidad'])[0]:.1f}%")
                v2.metric("Q5 - Competencia", f"{calcular_nps_detallado(df_base['Q5 - Competencia Vendedor'])[0]:.1f}%")
                v3.metric("Q8 - Info Pre-entrega", f"{calcular_nps_detallado(df_base['Q8 - Satisfacción información entre compra y entrega'])[0]:.1f}%")
            with stabs[1]:
                ct1, ct2 = st.columns(2)
                ct1.metric("Q7 - NPS Test Drive", f"{calcular_nps_detallado(df_base['Q7 - Satisfacción Test Drive'])[0]:.1f}%")
                # Gráfico torta rápido para Q6
                fig_q6 = px.pie(df_base, names='Q6 - Ofrecimiento Test Drive', title='Q6 - Ofrecimiento TD', hole=.4)
                ct2.plotly_chart(fig_q6, use_container_width=True)
            with stabs[3]:
                ce1, ce2 = st.columns(2)
                ce1.metric("Q11 - Momento Entrega", f"{calcular_nps_detallado(df_base['Q11 - Satisfacción Momento de la entrega'])[0]:.1f}%")
                ce2.metric("Q13 - Entrega General", f"{calcular_nps_detallado(df_base['Q13 - Satisfacción Entrega General'])[0]:.1f}%")

            # --- TABLA DE VERBALIZACIONES ---
            st.markdown("---")
            st.subheader(f"💬 Verbalizaciones (Q3) - {st.session_state.f}")
            df_v = df_base[["Fecha de ultimo contacto", "Nombre de cliente", "Q3 - Verbalización", "Vendedor", "Categoria_NPS"]].copy()
            if st.session_state.f != "Todos":
                df_v = df_v[df_v["Categoria_NPS"] == st.session_state.f]
            df_v["Fecha de ultimo contacto"] = df_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_v.drop(columns=['Categoria_NPS']).sort_values("Fecha de ultimo contacto", ascending=False), use_container_width=True, hide_index=True)

        with tab_vendedores:
            st.header("Ranking y Objetivos por Vendedor")
            resumen = []
            for vend, data in df_base.groupby("Vendedor"):
                n_v, p_v, ne_v, d_v, t_v = calcular_nps_detallado(data["Q1 - Satisfacción general"])
                resumen.append({"Vendedor": vend, "NPS Q1 %": n_v, "Cantidad": t_v, "Acción": calcular_faltante_94(p_v, d_v, t_v)})
            
            comp = pd.DataFrame(resumen).sort_values("NPS Q1 %", ascending=False)
            st.dataframe(comp.style.map(lambda x: 'color: red; font-weight: bold' if '🚨' in str(x) else 'color: green', subset=['Acción']), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error crítico: {e}")
