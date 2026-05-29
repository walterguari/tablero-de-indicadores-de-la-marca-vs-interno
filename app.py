import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

# --- FUNCIONES DE DATOS Y CÁLCULOS ---
@st.cache_data(ttl=600)  # Optimización: guarda en caché los datos por 10 minutos
def load_data(url):
    try:
        csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
        df = pd.read_csv(csv_url)
        df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
        
        def categorizar_nps(val):
            val = pd.to_numeric(val, errors='coerce')
            if val >= 9: return "Promotor"
            if val >= 7: return "Neutro"
            if val <= 6: return "Detractor"
            return "Sin Datos"
        
        df['Cat_Q1'] = df['Q1 - Satisfacción general'].apply(categorizar_nps)
        df['Cat_Q2'] = df['Q2 - Recomendación - Concesionario'].apply(categorizar_nps)
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
    if nps_actual >= 94: return "✅ Objetivo"
    x = (0.94 * total + detractores - promotores) / (1 - 0.94)
    return f"🚨 Faltan {math.ceil(x)}"

def get_bar_color(val):
    if val >= 94: return '#28a745'
    if val >= 90: return '#ffc107'
    return '#dc3545'

def crear_gauge_moderno(valor, titulo):
    color_viva = get_bar_color(valor)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': f"<b>{titulo}</b>", 'font': {'size': 22, 'color': '#333'}},
        number = {'suffix': "%", 'font': {'size': 45}},
        gauge = {
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': 94}
        }
    ))
    fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def crear_grafico_torta(df, columna, titulo):
    conteo = df[columna].value_counts().reset_index()
    conteo.columns = [columna, 'Cantidad']
    fig = px.pie(conteo, values='Cantidad', names=columna, title=titulo, hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label+value')
    return fig

# --- LÓGICA PRINCIPAL ---
try:
    df = load_data(sheet_url)
    if not df.empty:
        # --- SIDEBAR (FILTROS DINÁMICOS) ---
        st.sidebar.header("Filtros Globales")
        df['Anio'] = df["Fecha de ultimo contacto"].dt.year
        df['Mes_Num'] = df["Fecha de ultimo contacto"].dt.month
        
        # 1. Filtro de Año
        anios_disponibles = sorted(df['Anio'].dropna().unique().astype(int), reverse=True)
        anio_sel = st.sidebar.selectbox("Año", options=anios_disponibles)
        
        # 2. Filtro de Meses (Depende del Año)
        meses_n = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6: "Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        meses_disp_nums = sorted(df[df['Anio'] == anio_sel]['Mes_Num'].unique())
        meses_disp_nombres = [meses_n[m] for m in meses_disp_nums]
        
        meses_sel_nombres = st.sidebar.multiselect("Seleccione Mes(es)", options=meses_disp_nombres, default=meses_disp_nombres[-1:])
        meses_sel_nums = [k for k, v in meses_n.items() if v in meses_sel_nombres]

        # --- DATA FILTRADA POR TIEMPO PARA ACTUALIZAR LOS SIGUIENTES FILTROS ---
        df_time = df[(df["Anio"] == anio_sel) & (df["Mes_Num"].isin(meses_sel_nums))]

        # 3. Filtro de MARCA (Depende de Año y Mes)
        marcas_disponibles = sorted(df_time["MARCA"].unique())
        marcas = st.sidebar.multiselect("MARCA", options=marcas_disponibles, default=marcas_disponibles)

        # 4. Filtro de CANAL (Depende de Año, Mes y Marca)
        canales_disponibles = sorted(df_time[df_time["MARCA"].isin(marcas)]["Canal de Venta"].unique())
        canales = st.sidebar.multiselect("Canal de Venta", options=canales_disponibles, default=canales_disponibles)

        # --- DATA BASE FINAL ---
        df_base = df_time[(df_time["MARCA"].isin(marcas)) & (df_time["Canal de Venta"].isin(canales))]

        st.title("📊 Gestión de Calidad - Grupo Cenoa")
        
        # DEFINICIÓN DE PESTAÑAS (Optimizadas y Unificadas)
        tab_global, tab_unificada, tab_individual = st.tabs([
            "🏠 Monitor Global", 
            "👥 Tabla Unificada de Asesores", 
            "👤 Ficha Individual por Asesor"
        ])

        if 'filtro_col' not in st.session_state: st.session_state.filtro_col = "Cat_Q1"
        if 'filtro_val' not in st.session_state: st.session_state.filtro_val = "Todos"

        # ==========================================================
        # TAB: MONITOR GLOBAL
        # ==========================================================
        with tab_global:
            st.header(f"Resultados de: {', '.join(meses_sel_nombres)}")
            nps_q1, p_q1, n_q1, d_q1, t_q1 = calcular_nps_detallado(df_base['Q1 - Satisfacción general'])
            nps_q2, p_q2, n_q2, d_q2, _ = calcular_nps_detallado(df_base['Q2 - Recomendación - Concesionario'])

            c_q1, c_q2, c_tot = st.columns([2.2, 2.2, 0.6])
            with c_q1:
                st.plotly_chart(crear_gauge_moderno(nps_q1, "Q1 - SATISFACCIÓN"), use_container_width=True)
                col_b1, col_b2, col_b3 = st.columns(3)
                if col_b1.button(f"🟢 {p_q1}\nProm", key="q1_p"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q1", "Promotor"
                    st.rerun()
                if col_b2.button(f"🟡 {n_q1}\nNeu", key="q1_n"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q1", "Neutro"
                    st.rerun()
                if col_b3.button(f"🔴 {d_q1}\nDet", key="q1_d"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q1", "Detractor"
                    st.rerun()
            with c_q2:
                st.plotly_chart(crear_gauge_moderno(nps_q2, "Q2 - RECOMENDACIÓN"), use_container_width=True)
                col_b4, col_b5, col_b6 = st.columns(3)
                if col_b4.button(f"🟢 {p_q2}\nProm", key="q2_p"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q2", "Promotor"
                    st.rerun()
                if col_b5.button(f"🟡 {n_q2}\nNeu", key="q2_n"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q2", "Neutro"
                    st.rerun()
                if col_b6.button(f"🔴 {d_q2}\nDet", key="q2_d"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q2", "Detractor"
                    st.rerun()
            with c_tot:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.metric("Muestra", t_q1)
                if st.button("🔄 Ver\nTodos"): 
                    st.session_state.filtro_val = "Todos"
                    st.rerun()

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
                ct2.plotly_chart(crear_grafico_torta(df_base, 'Q6 - Ofrecimiento Test Drive', 'Q6 - Ofrecimiento TD'), use_container_width=True)
            with stabs[2]:
                cf1, cf2 = st.columns(2)
                cf1.metric("Q10 - NPS Financiación", f"{calcular_nps_detallado(df_base['Q10 - Satisfacción Financiación utilizada'])[0]:.1f}%")
                cf2.plotly_chart(crear_grafico_torta(df_base, 'Q9 - Financiación utilizada', 'Mix Financiación'), use_container_width=True)
            with stabs[3]:
                ce1, ce2 = st.columns(2)
                ce1.metric("Q11 - Momento Entrega", f"{calcular_nps_detallado(df_base['Q11 - Satisfacción Momento de la entrega'])[0]:.1f}%")
                ce2.metric("Q13 - Entrega General", f"{calcular_nps_detallado(df_base['Q13 - Satisfacción Entrega General'])[0]:.1f}%")

            st.markdown("---")
            label_f = "Todos los comentarios" if st.session_state.filtro_val == "Todos" else f"Comentarios: {st.session_state.filtro_val} ({st.session_state.filtro_col.replace('Cat_', '')})"
            st.subheader(f"💬 Verbalizaciones (Q3) - {label_f}")
            df_v = df_base[["Fecha de ultimo contacto", "Nombre de cliente", "Q3 - Verbalización", "Vendedor", "Cat_Q1", "Cat_Q2"]].copy()
            if st.session_state.filtro_val != "Todos":
                df_v = df_v[df_v[st.session_state.filtro_col] == st.session_state.filtro_val]
            
            df_v = df_v.sort_values("Fecha de ultimo contacto", ascending=False)
            df_v["Fecha de ultimo contacto"] = df_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_v[["Fecha de ultimo contacto", "Nombre de cliente", "Q3 - Verbalización", "Vendedor"]], use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 2: TABLA MASTER UNIFICADA (MEJORAS 3 Y 4)
        # ==========================================================
        with tab_unificada:
            st.header("Ranking Ejecutivo Unificado (Q2, Q4, Q5)")
            st.markdown("Consolidado interactivo de asesores comerciales. Podés hacer clic en los encabezados para ordenar por cualquier indicador.")
            
            if not df_base.empty:
                resumen_master = []
                for vend, data in df_base.groupby("Vendedor"):
                    n_q2, p_q2, _, d_q2, t_q2 = calcular_nps_detallado(data["Q2 - Recomendación - Concesionario"])
                    n_q4, _, _, _, _ = calcular_nps_detallado(data["Q4 - Cortesía y amabilidad"])
                    n_q5, _, _, _, _ = calcular_nps_detallado(data["Q5 - Competencia Vendedor"])
                    
                    resumen_master.append({
                        "Vendedor": vend,
                        "NPS Recomendación (Q2)": round(n_q2, 1),
                        "Faltante Obj. Q2": calcular_faltante_94(p_q2, d_q2, t_q2),
                        "NPS Cortesía (Q4)": round(n_q4, 1),
                        "NPS Competencia (Q5)": round(n_q5, 1),
                        "Encuestas Recibidas": t_q2
                    })
                
                df_master = pd.DataFrame(resumen_master).sort_values("NPS Recomendación (Q2)", ascending=False)
                
                # Formato visual condicional (Estilo BI / Semáforos)
                def color_celda_nps(val):
                    try:
                        v = float(val)
                        if v >= 94: return 'background-color: #d4edda; color: #155724; font-weight: bold'
                        if v >= 90: return 'background-color: #fff3cd; color: #856404; font-weight: bold'
                        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                    except:
                        return ''

                df_styled = df_master.style.map(color_celda_nps, subset=["NPS Recomendación (Q2)", "NPS Cortesía (Q4)", "NPS Competencia (Q5)"])\
                                           .map(lambda x: 'color: #721c24; font-weight: bold' if '🚨' in str(x) else 'color: #155724', subset=['Faltante Obj. Q2'])
                
                st.dataframe(df_styled, use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 3: FICHA INDIVIDUAL POR ASESOR (MEJORAS 1 Y 2)
        # ==========================================================
        with tab_individual:
            st.header("Análisis de Evolución por Asesor Comercial")
            
            # Filtro para elegir un vendedor específico
            vendedores_disponibles = sorted(df_base["Vendedor"].dropna().unique())
            if vendedores_disponibles:
                vendedor_sel = st.selectbox("Seleccione el Asesor a Evaluar", options=vendedores_disponibles)
                
                # Datos del vendedor actual filtrados por marca y canal de arriba
                df_vend = df_base[df_base["Vendedor"] == vendedor_sel]
                
                # --- CÁLCULO DE ALERTAS MES CONTRA MES (MEJORA 2) ---
                # Conseguimos todo el historial temporal de este vendedor para evaluar tendencia
                df_vend_full = df[(df["Vendedor"] == vendedor_sel) & (df["MARCA"].isin(marcas)) & (df["Canal de Venta"].isin(canales))].copy()
                df_vend_full["Periodo"] = df_vend_full["Fecha de ultimo contacto"].dt.to_period("M")
                
                resumen_mensual = []
                for per, data_m in df_vend_full.groupby("Periodo"):
                    n_m, _, _, _, _ = calcular_nps_detallado(data_m["Q2 - Recomendación - Concesionario"])
                    resumen_mensual.append({"Periodo_Str": str(per), "Periodo": per, "NPS Q2": n_m})
                
                df_evolucion = pd.DataFrame(resumen_mensual).sort_values("Periodo")
                
                # Metricas clave con flecha de tendencia
                st.markdown(f"### Desempeño Actual de: **{vendedor_sel}**")
                
                v_q2, pv2, _, dv2, tv2 = calcular_nps_detallado(df_vend["Q2 - Recomendación - Concesionario"])
                v_q4, _, _, _, _ = calcular_nps_detallado(df_vend["Q4 - Cortesía y amabilidad"])
                v_q5, _, _, _, _ = calcular_nps_detallado(df_vend["Q5 - Competencia Vendedor"])
                
                # Determinar flechas de tendencia comparando el último periodo contra el anterior
                alerta_q2 = ""
                if len(df_evolucion) >= 2:
                    ultimo_nps = df_evolucion.iloc[-1]["NPS Q2"]
                    anterior_nps = df_evolucion.iloc[-2]["NPS Q2"]
                    if ultimo_nps > anterior_nps:
                        alerta_q2 = f"⬆️ (+{ultimo_nps - anterior_nps:.1f}% vs mes ant.)"
                    elif ultimo_nps < anterior_nps:
                        alerta_q2 = f"⬇️ ({ultimo_nps - anterior_nps:.1f}% vs mes ant.)"
                    else:
                        alerta_q2 = "➡️ (Sin cambios)"

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("NPS Recomendación (Q2)", f"{v_q2:.1f}%", help="Métrica principal de recomendación")
                m2.metric("Tendencia Q2", alerta_q2 if alerta_q2 else "Muestra inicial", delta_color="off")
                m3.metric("NPS Cortesía (Q4)", f"{v_q4:.1f}%")
                m4.metric("NPS Competencia (Q5)", f"{v_q5:.1f}%")
                
                # --- GRÁFICO DE LÍNEAS TEMPORAL (MEJORA 1) ---
                st.markdown("---")
                st.subheader("📈 Evolución Histórica Mensual (NPS Q2)")
                if not df_evolucion.empty:
                    fig_linea = px.line(
                        df_evolucion, 
                        x="Periodo_Str", 
                        y="NPS Q2", 
                        text=df_evolucion["NPS Q2"].round(1).astype(str) + "%",
                        labels={"Periodo_Str": "Mes de Contacto", "NPS Q2": "NPS Recomendación %"},
                        markers=True
                    )
                    fig_linea.add_hline(y=94, line_dash="dash", line_color="green", annotation_text="Objetivo Cenoa (94%)")
                    fig_linea.update_traces(textposition="top center", line=dict(color='#007bff', width=3))
                    fig_linea.update_layout(yaxis=dict(range=[-10, 110]), height=320, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_linea, use_container_width=True, key="grafico_evolucion_vendedor")
                else:
                    st.info("Sin historial suficiente para trazar línea de tiempo.")
                
                # --- EXCLUSIVO VERBALIZACIONES DEL ASESOR ---
                st.markdown("---")
                st.subheader(f"💬 Comentarios de Clientes asignados a {vendedor_sel}")
                df_v_individual = df_vend[["Fecha de ultimo contacto", "Nombre de cliente", "Q3 - Verbalización", "Q2 - Recomendación - Concesionario"]].copy()
                df_v_individual = df_v_individual.sort_values("Fecha de ultimo contacto", ascending=False)
                df_v_individual["Fecha de ultimo contacto"] = df_v_individual["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_v_individual.rename(columns={"Q2 - Recomendación - Concesionario": "Nota Q2"}), 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.warning("No se encontraron asesores con los filtros seleccionados.")

except Exception as e:
    st.error(f"Error crítico en la ejecución del tablero: {e}")
