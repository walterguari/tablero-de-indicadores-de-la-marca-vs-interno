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
        
        # Columna de categoría NPS para los botones de filtro
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
    nps_actual = ((promotores - detractores) / total) * 100
    if nps_actual >= 94:
        return "✅ Objetivo cumplido. ¡Seguir así!"
    x = (0.94 * total + detractores - promotores) / (1 - 0.94)
    necesarios = math.ceil(x)
    return f"🚨 Faltan {necesarios} encuestas (9-10) para el 94%"

# --- DISEÑO DE RELOJ ---
def crear_gauge_moderno(valor, titulo):
    color_viva = '#28a745' if valor >= 94 else ('#ffc107' if valor >= 90 else '#dc3545')
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': f"<span style='font-size:22px; font-weight:bold; color:#333'>{titulo}</span>", 'padding': {'b': 20}},
        number = {'suffix': "%", 'font': {'size': 45, 'color': '#333'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickvals': [], 'showticklabels': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': 94}
        }
    ))
    fig.update_layout(height=300, margin=dict(l=30, r=30, t=20, b=0), paper_bgcolor='rgba(0,0,0,0)')
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
    if not df.empty:
        # Filtros laterales
        st.sidebar.header("Filtros Globales")
        df['Anio'] = df["Fecha de ultimo contacto"].dt.year
        df['Mes_Num'] = df["Fecha de ultimo contacto"].dt.month
        
        lista_anios = sorted(df['Anio'].dropna().unique().astype(int), reverse=True)
        anio_sel = st.sidebar.selectbox("Seleccione Año", options=lista_anios)
        
        meses_nombre = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
        meses_disp = sorted(df[df['Anio'] == anio_sel]['Mes_Num'].unique())
        mes_sel_nombre = st.sidebar.selectbox("Seleccione Mes", options=[meses_nombre[m] for m in meses_disp])
        mes_sel_num = [k for k, v in meses_nombre.items() if v == mes_sel_nombre][0]

        marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
        canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())

        df_base = df[(df["Anio"] == anio_sel) & (df["Mes_Num"] == mes_sel_num) & 
                     (df["MARCA"].isin(marca)) & (df["Canal de Venta"].isin(canal))]

        st.title("📊 Gestión de Calidad - Grupo Cenoa")
        p1, p2 = st.tabs(["🏠 Monitor Global", "👤 Rendimiento por Vendedor"])

        with p1:
            st.header(f"Resultados Globales - {mes_sel_nombre} {anio_sel}")
            nps_q1, prom_q1, neu_q1, det_q1, total_q1 = calcular_nps_detallado(df_base['Q1 - Satisfacción general'])
            nps_q2, _, _, _, _ = calcular_nps_detallado(df_base['Q2 - Recomendación - Concesionario'])
            
            # --- RELOJES Y BOTONES MÉTRICOS ---
            c_rel1, c_rel2 = st.columns(2)
            
            with c_rel1:
                st.plotly_chart(crear_gauge_moderno(nps_q1, "Q1 - SATISFACCIÓN"), use_container_width=True)
                st.write("Ver comentarios de:")
                col_b1, col_b2, col_b3 = st.columns(3)
                btn_prom = col_b1.button(f"🟢 {prom_q1} Promotores")
                btn_neu = col_b2.button(f"🟡 {neu_q1} Neutros")
                btn_det = col_b3.button(f"🔴 {det_q1} Detractores")
                
            with c_rel2:
                st.plotly_chart(crear_gauge_moderno(nps_q2, "Q2 - RECOMENDACIÓN"), use_container_width=True)
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                st.metric("Total Muestra", total_q1)

            # Lógica de filtro para la tabla
            if 'filtro' not in st.session_state: st.session_state.filtro = "Todos"
            if btn_prom: st.session_state.filtro = "Promotor"
            if btn_neu: st.session_state.filtro = "Neutro"
            if btn_det: st.session_state.filtro = "Detractor"
            if st.button("🔄 Ver Todos los comentarios"): st.session_state.filtro = "Todos"

            st.markdown("<br>", unsafe_allow_html=True)
            sub_tabs = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
            
            with sub_tabs[0]:
                v1, v2, v3 = st.columns(3)
                v1.metric("Q4 - Cortesía", f"{calcular_nps_detallado(df_base['Q4 - Cortesía y amabilidad'])[0]:.1f}%")
                v2.metric("Q5 - Competencia", f"{calcular_nps_detallado(df_base['Q5 - Competencia Vendedor'])[0]:.1f}%")
                v3.metric("Q8 - Info Pre-entrega", f"{calcular_nps_detallado(df_base['Q8 - Satisfacción información entre compra y entrega'])[0]:.1f}%")
            # ... (Resto de sub-tabs cargan igual)

            st.markdown("---")
            st.subheader(f"💬 Verbalizaciones (Q3) - Mostrando: {st.session_state.filtro}")
            
            df_verbal = df_base[["Fecha de ultimo contacto", "Nombre de cliente", "Q3 - Verbalización", "Vendedor", "Categoria_NPS"]].copy()
            if st.session_state.filtro != "Todos":
                df_verbal = df_verbal[df_verbal["Categoria_NPS"] == st.session_state.filtro]
            
            df_verbal["Fecha de ultimo contacto"] = df_verbal["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_verbal.drop(columns=['Categoria_NPS']).sort_values("Fecha de ultimo contacto", ascending=False), 
                         use_container_width=True, hide_index=True)

        with p2:
            st.header("Análisis de Objetivos Stellantis (Mínimo 94%)")
            resumen = []
            for vend, data in df_base.groupby("Vendedor"):
                n_v, p_v, ne_v, d_v, t_v = calcular_nps_detallado(data["Q1 - Satisfacción general"])
                accion = calcular_faltante_94(p_v, d_v, t_v)
                resumen.append({"Vendedor": vend, "NPS Q1 %": n_v, "Cantidad": t_v, "Acción/Objetivo": accion})
            
            comp = pd.DataFrame(resumen).sort_values("NPS Q1 %", ascending=False)
            st.dataframe(comp.style.map(lambda x: 'color: red; font-weight: bold' if '🚨' in str(x) else 'color: green', subset=['Acción/Objetivo']), 
                         use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Ocurrió un error: {e}")
