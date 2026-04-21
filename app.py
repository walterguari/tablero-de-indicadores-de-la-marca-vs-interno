import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

# URL de tu Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

# --- FUNCIONES DE DATOS Y CÁLCULOS ---
def load_data(url):
    try:
        csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
        df = pd.read_csv(csv_url)
        df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
        
        # Categorización para filtros
        def categorizar(v):
            v = pd.to_numeric(v, errors='coerce')
            if v >= 9: return "Promotor"
            if v >= 7: return "Neutro"
            if v <= 6: return "Detractor"
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
    if nps_actual >= 94:
        return "✅ ¡Excelente! Objetivo Stellantis cumplido."
    x = (0.94 * total + detractores - promotores) / (1 - 0.94)
    necesarios = math.ceil(x)
    return f"🚨 Faltan {necesarios} encuestas (9-10) para el 94%"

def obtener_color_rango(valor):
    if valor >= 94: return '#28a745'
    if valor >= 90: return '#ffc107'
    return '#dc3545'

def crear_gauge_moderno(valor, titulo):
    color_viva = obtener_color_rango(valor)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': f"<b>{titulo}</b>", 'font': {'size': 22, 'color': '#333'}},
        number = {'suffix': "%", 'font': {'size': 45, 'color': '#333'}},
        gauge = {
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.8,
                'value': 94
            }
        }
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=30, r=30, t=60, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def crear_grafico_torta(df, columna, titulo):
    conteo = df[columna].value_counts().reset_index()
    conteo.columns = [columna, 'Cantidad']
    fig = px.pie(conteo, values='Cantidad', names=columna, title=titulo, hole=0.4, 
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label+value')
    return fig

# --- LÓGICA DE LA APLICACIÓN ---
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
        meses_disponibles = sorted(df[df['Anio'] == anio_sel]['Mes_Num'].unique())
        mes_sel_nombre = st.sidebar.selectbox("Seleccione Mes", options=[meses_nombre[m] for m in meses_disponibles])
        mes_sel_num = [k for k, v in meses_nombre.items() if v == mes_sel_nombre][0]

        marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
        canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())

        # Filtrado base
        df_base = df[(df["Anio"] == anio_sel) & (df["Mes_Num"] == mes_sel_num) & 
                      (df["MARCA"].isin(marca)) & (df["Canal de Venta"].isin(canal))]

        st.title("📊 Gestión de Calidad - Grupo Cenoa")
        p1, p2 = st.tabs(["🏠 Monitor Global", "👤 Rendimiento por Vendedor"])

        with p1:
            st.header(f"Resultados Globales - {mes_sel_nombre} {anio_sel}")
            nps_q1, p_q1, n_q1, d_q1, total_q1 = calcular_nps_detallado(df_base['Q1 - Satisfacción general'])
            nps_q2, _, _, _, _ = calcular_nps_detallado(df_base['Q2 - Recomendación - Concesionario'])
            
            # --- DASHBOARD SUPERIOR ---
            col_g1, col_g2, col_g3 = st.columns([2.5, 2.5, 1.2])
            
            with col_g1:
                st.plotly_chart(crear_gauge_moderno(nps_q1, "Q1 - SATISFACCIÓN"), use_container_width=True)
                
                # --- BOTONES DE FILTRADO INTERACTIVO ---
                st.write("**Ver comentarios de:**")
                # Inicializar estado del filtro
                if 'filtro_comentarios' not in st.session_state:
                    st.session_state.filtro_comentarios = "Todos"

                c_btn1, c_btn2, c_btn3 = st.columns(3)
                if c_btn1.button(f"🟢 {p_q1} Promotores"):
                    st.session_state.filtro_comentarios = "Promotor"
                if c_btn2.button(f"🟡 {n_q1} Neutros"):
                    st.session_state.filtro_comentarios = "Neutro"
                if c_btn3.button(f"🔴 {d_q1} Detractores"):
                    st.session_state.filtro_comentarios = "Detractor"

            with col_g2:
                st.plotly_chart(crear_gauge_moderno(nps_q2, "Q2 - RECOMENDACIÓN"), use_container_width=True)
                if st.button("🔄 Ver todos los comentarios"):
                    st.session_state.filtro_comentarios = "Todos"

            with col_g3:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.metric("Total Muestra", total_q1)

            # --- SUB-TABS INDICADORES ---
            st.markdown("<br>", unsafe_allow_html=True)
            sub_tabs = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
            
            with sub_tabs[0]:
                v1, v2, v3 = st.columns(3)
                v1.metric("Q4 - Cortesía", f"{calcular_nps_detallado(df_base['Q4 - Cortesía y amabilidad'])[0]:.1f}%")
                v2.metric("Q5 - Competencia", f"{calcular_nps_detallado(df_base['Q5 - Competencia Vendedor'])[0]:.1f}%")
                v3.metric("Q8 - Info Pre-entrega", f"{calcular_nps_detallado(df_base['Q8 - Satisfacción información entre compra y entrega'])[0]:.1f}%")
            with sub_tabs[1]:
                ct1, ct2 = st.columns(2)
                with ct1: st.plotly_chart(crear_grafico_torta(df_base, "Q6 - Ofrecimiento Test Drive", "Q6 - Ofrecimiento TD"), use_container_width=True)
                with ct2: st.metric("Q7 - NPS Test Drive", f"{calcular_nps_detallado(df_base['Q7 - Satisfacción Test Drive'])[0]:.1f}%")
            with sub_tabs[2]:
                cf1, cf2 = st.columns(2)
                with cf1: st.plotly_chart(crear_grafico_torta(df_base, "Q9 - Financiación utilizada", "Q9 - Tipo de Pago"), use_container_width=True)
                with cf2: st.metric("Q10 - NPS Financiación", f"{calcular_nps_detallado(df_base['Q10 - Satisfacción Financiación utilizada'])[0]:.1f}%")
            with sub_tabs[3]:
                ce1, ce2 = st.columns(2)
                ce1.metric("Q11 - Momento Entrega", f"{calcular_nps_detallado(df_base['Q11 - Satisfacción Momento de la entrega'])[0]:.1f}%")
                ce2.metric("Q13 - Entrega General", f"{calcular_nps_detallado(df_base['Q13 - Satisfacción Entrega General'])[0]:.1f}%")

            # --- TABLA DE VERBALIZACIONES FILTRADA ---
            st.markdown("---")
            st.subheader(f"💬 Verbalizaciones (Q3) - Mostrando: {st.session_state.filtro_comentarios}")
            
            df_verbal = df_base[["Fecha de ultimo contacto", "Nombre de cliente", "Q3 - Verbalización", "Vendedor", "Categoria_NPS"]].copy()
            
            # Aplicar filtro de los botones
            if st.session_state.filtro_comentarios != "Todos":
                df_verbal = df_verbal[df_verbal["Categoria_NPS"] == st.session_state.filtro_comentarios]
            
            df_verbal["Fecha de ultimo contacto"] = df_verbal["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_verbal.drop(columns=['Categoria_NPS']).sort_values("Fecha de ultimo contacto", ascending=False), use_container_width=True, hide_index=True)

        with p2:
            st.header("Análisis de Objetivos Stellantis (Mínimo 94%)")
            if not df_base.empty:
                resumen = []
                for vend, data in df_base.groupby("Vendedor"):
                    nps_v, prom_v, neut_v, detr_v, total_v = calcular_nps_detallado(data["Q1 - Satisfacción general"])
                    accion = calcular_faltante_94(prom_v, detr_v, total_v)
                    resumen.append({"Vendedor": vend, "NPS Q1 %": nps_v, "Cantidad": total_v, "Acción/Objetivo": accion})
                
                comp = pd.DataFrame(resumen).sort_values("NPS Q1 %", ascending=False)
                
                fig_rank = px.bar(comp, x="Vendedor", y="NPS Q1 %", text="NPS Q1 %", color="NPS Q1 %", range_y=[0, 110],
                                  color_continuous_scale=[[0, '#dc3545'], [0.899, '#dc3545'], [0.90, '#ffc107'], [0.939, '#ffc107'], [0.94, '#28a745'], [1, '#28a745']])
                fig_rank.add_hline(y=94, line_dash="dash", line_color="black", annotation_text="Objetivo 94%")
                fig_rank.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                st.plotly_chart(fig_rank, use_container_width=True)

                st.subheader("Tabla de Acción Inmediata")
                def estilo_celda(val):
                    color = 'red' if '🚨' in str(val) else 'green'
                    return f'color: {color}; font-weight: bold'
                
                st.dataframe(comp[["Vendedor", "NPS Q1 %", "Cantidad", "Acción/Objetivo"]].style.map(estilo_celda, subset=['Acción/Objetivo']), 
                              use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error crítico en la aplicación: {e}")
