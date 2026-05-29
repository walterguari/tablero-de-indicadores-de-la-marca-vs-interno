import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tablero de Indicadores - Autociel", layout="wide")

URL_MARCA = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"
URL_INTERNA = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=1131519764"

# --- FUNCIONES DE DATOS Y CÁLCULOS ---
def limpiar_comas_a_numerico(serie):
    """Convierte strings con comas a números flotantes legibles por Python"""
    if serie is None or serie.empty:
        return pd.Series(dtype=float)
    return pd.to_numeric(serie.astype(str).str.replace(',', '.'), errors='coerce')

@st.cache_data(ttl=600)
def load_data(url, tipo_base):
    try:
        csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=").replace("/edit?gid=", "/export?format=csv&gid=")
        df = pd.read_csv(csv_url)
        
        # Normalización estructural según el origen de datos
        if tipo_base == "Encuestas de Marca":
            df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
        else:
            # Base Interna
            df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de último contacto"], dayfirst=True, errors='coerce')
            df["MARCA"] = df["MARCA"]
            df["Canal de Venta"] = df["CANAL DE VENTA"]
            df["Vendedor"] = df["VENDEDOR"]
            
            # Mapeo de la columna cliente para la tabla de comentarios
            if "Cliente" in df.columns:
                df["Nombre de cliente"] = df["Cliente"]
            elif "Nombre de cliente" not in df.columns:
                df["Nombre de cliente"] = "Cliente Autociel"
                
        return df
    except Exception as e:
        st.error(f"Error al cargar datos ({tipo_base}): {e}")
        return pd.DataFrame()

def calcular_nps_detallado(serie):
    serie_limpia = limpiar_comas_a_numerico(serie).dropna()
    total = len(serie_limpia)
    if total == 0: return 0, 0, 0, 0, 0
    promotores = (serie_limpia >= 9).sum()
    neutros = ((serie_limpia >= 7) & (serie_limpia <= 8)).sum()
    detractores = (serie_limpia <= 6).sum()
    nps = ((promotores - detractores) / total) * 100
    return nps, promotores, neutros, detractores, total

def calcular_csi_directo_porcentaje(serie):
    serie_limpia = limpiar_comas_a_numerico(serie).dropna()
    total = len(serie_limpia)
    if total == 0: return 0.0, 0
    promedio_porcentaje = (serie_limpia.mean()) * 10
    return promedio_porcentaje, total

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
        title = {'text': f"<b>{titulo}</b>", 'font': {'size': 13, 'color': '#333'}},
        number = {'suffix': "%", 'font': {'size': 28}, 'valueformat': '.1f'},
        gauge = {
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': 94}
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def crear_grafico_torta(df, columna_o_keyword, titulo):
    columna_real = None
    for col in df.columns:
        if columna_o_keyword.lower() in col.lower():
            columna_real = col
            break
            
    if not columna_real: 
        fig = go.Figure()
        fig.update_layout(title=titulo, annotations=[dict(text="Columna no encontrada", showarrow=False, font=dict(size=12))])
        return fig
    
    df_torta = df[[columna_real]].dropna().copy()
    df_torta[columna_real] = df_torta[columna_real].astype(str).str.strip().str.upper()
    
    if df_torta.empty:
        fig = go.Figure()
        fig.update_layout(title=titulo, annotations=[dict(text="Sin respuestas válidas", showarrow=False, font=dict(size=13))])
        return fig
        
    conteo = df_torta[columna_real].value_counts().reset_index()
    conteo.columns = ['Respuesta', 'Cantidad']
    
    conteo['Respuesta'] = conteo['Respuesta'].replace({'SÍ': 'SI', 'SÍ, SE OFRECIÓ': 'SI', 'CONTACTADO': 'SI'})
    conteo['Respuesta'] = conteo['Respuesta'].replace({'NO CONTACTADO': 'NO'})
    
    total_respuestas = conteo['Cantidad'].sum()
    
    if 'SI' in conteo['Respuesta'].values:
        cant_si = conteo[conteo['Respuesta'] == 'SI']['Cantidad'].sum()
        pct_si = (cant_si / total_respuestas) * 100 if total_respuestas > 0 else 0.0
        label_centro = "Sí"
    else:
        cant_si = conteo.iloc[0]['Cantidad']
        pct_si = (cant_si / total_respuestas) * 100 if total_respuestas > 0 else 0.0
        label_centro = str(conteo.iloc[0]['Respuesta']).title()
    
    colores_map = {'SI': '#28a745', 'NO': '#dc3545'}
    
    fig = px.pie(
        conteo, 
        values='Cantidad', 
        names='Respuesta', 
        title=titulo, 
        hole=0.6,
        color='Respuesta',
        color_discrete_map=colores_map if 'SI' in conteo['Respuesta'].values else None,
        color_discrete_sequence=px.colors.qualitative.Pastel if 'SI' not in conteo['Respuesta'].values else None
    )
    fig.update_traces(textinfo='percent+label', textposition='outside')
    
    fig.update_layout(
        height=220, 
        margin=dict(l=10, r=10, t=40, b=10), 
        showlegend=False,
        annotations=[dict(
            text=f"<b>{pct_si:.1f}%</b><br><span style='font-size:11px;color:#666;font-weight:normal;'>{label_centro}</span>", 
            showarrow=False, 
            font=dict(size=20, color='#28a745' if label_centro == "Sí" else '#007bff')
        )]
    )
    return fig

# --- LÓGICA PRINCIPAL ---
try:
    # Variables de control para filtros interactivos por clicks en botones
    if 'filtro_val_marca' not in st.session_state: st.session_state.filtro_val_marca = "Todos"
    if 'filtro_col_marca' not in st.session_state: st.session_state.filtro_col_marca = "Cat_Filtro_Dinamica"
    if 'filtro_val_interna' not in st.session_state: st.session_state.filtro_val_interna = "Todos"
    if 'filtro_col_interna' not in st.session_state: st.session_state.filtro_col_interna = "Cat_Filtro_Dinamica"

    # --- CARGA PARALELA DE AMBAS BASES ---
    df_m_raw = load_data(URL_MARCA, "Encuestas de Marca")
    df_i_raw = load_data(URL_INTERNA, "Encuestas Internas")
    
    if not df_m_raw.empty and not df_i_raw.empty:
        
        # --- DEFINICIÓN DE MAPAS DE COLUMNAS ---
        MAPA_M = {
            'q1': 'Q1 - Satisfacción general', 'q2': 'Q2 - Recomendación - Concesionario', 'q3': 'Q3 - Verbalización',
            'q4': 'Q4 - Cortesía y amabilidad', 'q5': 'Q5 - Competencia Vendedor', 'q6': 'Q6 - Ofrecimiento Test Drive',
            'q8': 'Q8 - Satisfacción información entre compra y entrega', 'q11': 'Q11 - Satisfacción Momento de la entrega',
            'q14': 'Q14 - Contactado', 'q15': 'Q15 - Satisfacción con el Contacto',
            'lbl_q1': 'Q1 - SATISFACCIÓN (NPS)', 'lbl_q2': 'Q2 - RECOMENDACIÓN (NPS)'
        }
        
        MAPA_I = {
            'q1': 'CSI', 'q2': '1. Basándose en su experiencia de compra, ¿Recomendaría el Concesionario a Familiares y amigos?',
            'q3': 'COMENTARIO DEL CLIENTE', 'q4': '2. ¿Cómo califica la cortesía y amabilidad del Vendedor / Asesor Comercial?',
            'q5': None, 'q6': '3. ¿Le han ofrecido una prueba de manejo?',
            'q8': '4. ¿Cómo califica la información facilitada entre la compra y la entrega de su vehículo nuevo? (Comunicación y explicación de tramites administrativos)',
            'q11': '5. ¿Cómo califica la presentación de su 0KM al momento de la entrega? (explicaciones de las características, la limpieza y la presentación con el vehículo, entre otros aspectos.)',
            'q14': 'contacto del concesionario posterior', 'q15': '7. ¿Cuán satisfied se encuentra con el contacto posterior realizado por el concesionario?',
            'lbl_q1': 'CSI GENERAL (PROMEDIO %)', 'lbl_q2': '1. RECOMENDACIÓN (NPS)'
        }

        # --- PRE-CATEGORIZACIÓN DE COLUMNAS PARA CLICKS ---
        def cat_valores(v):
            if pd.isna(v): return "Sin Datos"
            v_n = pd.to_numeric(v, errors='coerce')
            if v_n >= 9.0: return "Promotor"
            if v_n >= 7.0: return "Neutro"
            return "Detractor"
            
        df_m_raw['Cat_Filtro_Dinamica'] = df_m_raw[MAPA_M['q1']].apply(cat_valores)
        df_m_raw['Cat_Filtro_Q2'] = df_m_raw[MAPA_M['q2']].apply(cat_valores)
        
        df_i_raw['Cat_Filtro_Dinamica'] = limpiar_comas_a_numerico(df_i_raw[MAPA_I['q1']]).apply(cat_valores)
        df_i_raw['Cat_Filtro_Q2'] = limpiar_comas_a_numerico(df_i_raw[MAPA_I['q2']]).apply(cat_valores)

        # --- SIDEBAR (FILTROS GLOBALES UNIFICADOS) ---
        st.sidebar.header("Filtros Globales")
        
        # Combinamos fechas para extraer universos de años/meses completos
        df_m_raw['Anio'] = df_m_raw["Fecha de ultimo contacto"].dt.year
        df_m_raw['Mes_Num'] = df_m_raw["Fecha de ultimo contacto"].dt.month
        df_i_raw['Anio'] = df_i_raw["Fecha de ultimo contacto"].dt.year
        df_i_raw['Mes_Num'] = df_i_raw["Fecha de ultimo contacto"].dt.month
        
        anios_validos = sorted(list(set(df_m_raw['Anio'].dropna().unique()) | set(df_i_raw['Anio'].dropna().unique())), reverse=True)
        anio_sel = st.sidebar.selectbox("Año", options=anios_validos if anios_validos else [2026], key="sb_anio_unificado")
        
        meses_n = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6: "Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        meses_m = set(df_m_raw[df_m_raw['Anio'] == anio_sel]['Mes_Num'].unique())
        meses_i = set(df_i_raw[df_i_raw['Anio'] == anio_sel]['Mes_Num'].unique())
        meses_disp_nums = sorted(list(meses_m | meses_i))
        meses_disp_nombres = [meses_n[m] for m in meses_disp_nums] if meses_disp_nums else ["Mayo"]
        
        meses_sel_nombres = st.sidebar.multiselect("Seleccione Mes(es)", options=meses_disp_nombres, default=meses_disp_nombres[-1:], key="sb_meses_unificado")
        meses_sel_nums = [k for k, v in meses_n.items() if v in meses_sel_nombres]

        # Aplicamos tiempo
        df_m_time = df_m_raw[(df_m_raw["Anio"] == anio_sel) & (df_m_raw["Mes_Num"].isin(meses_sel_nums))]
        df_i_time = df_i_raw[(df_i_raw["Anio"] == anio_sel) & (df_i_raw["Mes_Num"].isin(meses_sel_nums))]

        # Universo Marcas y Canales combinados
        marcas_m = set(df_m_time["MARCA"].dropna().unique())
        marcas_i = set(df_i_time["MARCA"].dropna().unique())
        marcas_disponibles = sorted(list(marcas_m | marcas_i))
        marcas = st.sidebar.multiselect("MARCA", options=marcas_disponibles, default=marcas_disponibles, key="sb_marcas_unificado")

        canales_m = set(df_m_time[df_m_time["MARCA"].isin(marcas)]["Canal de Venta"].dropna().unique())
        canales_i = set(df_i_time[df_i_time["MARCA"].isin(marcas)]["Canal de Venta"].dropna().unique())
        canales_disponibles = sorted(list(canales_m | canales_i))
        canales = st.sidebar.multiselect("Canal de Venta", options=canales_disponibles, default=canales_disponibles, key="sb_canales_unificado")

        # Dataframes Base finales ya filtrados por el SideBar
        df_m_base = df_m_time[(df_m_time["MARCA"].isin(marcas)) & (df_m_time["Canal de Venta"].isin(canales))]
        df_i_base = df_i_time[(df_i_time["MARCA"].isin(marcas)) & (df_i_time["Canal de Venta"].isin(canales))]

        st.title(f"📊 Control de Calidad Autociel - Monitor Unificado")
        
        tab_global, tab_unificada, tab_individual = st.tabs([
            "🏠 Monitor Global (En Paralelo)", 
            "👥 Tabla Unificada de Asesores", 
            "👤 Ficha Individual por Asesor"
        ])

        # ==========================================================
        # TAB 1: MONITOR GLOBAL (DIVIDIDO EN 2 COLUMNAS)
        # ==========================================================
        with tab_global:
            
            # Layout Principal: Dos Grandes Columnas
            col_pantalla_marca, col_pantalla_interna = st.columns([1, 1])
            
            # --- COLUMNA IZQUIERDA: ENCUESTAS DE MARCA ---
            with col_pantalla_marca:
                st.subheader("🏢 Encuestas de Marca")
                
                val_m_q1, p_m_q1, n_m_q1, d_m_q1, t_m_q1 = calcular_nps_detallado(df_m_base[MAPA_M['q1']])
                nps_m_q2, p_m_q2, n_m_q2, d_m_q2, _ = calcular_nps_detallado(df_m_base[MAPA_M['q2']])
                
                c_m1, c_m2, c_mt = st.columns([2, 2, 0.8])
                with c_m1:
                    st.plotly_chart(crear_gauge_moderno(val_m_q1, MAPA_M['lbl_q1']), use_container_width=True, key="g_m_q1")
                    b1, b2, b3 = st.columns(3)
                    if b1.button(f"🟢 {p_m_q1}", key="bm_q1_p"): st.session_state.filtro_col_marca = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_marca = "Promotor"; st.rerun()
                    if b2.button(f"🟡 {n_m_q1}", key="bm_q1_n"): st.session_state.filtro_col_marca = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_marca = "Neutro"; st.rerun()
                    if b3.button(f"🔴 {d_m_q1}", key="bm_q1_d"): st.session_state.filtro_col_marca = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_marca = "Detractor"; st.rerun()
                with c_m2:
                    st.plotly_chart(crear_gauge_moderno(nps_m_q2, MAPA_M['lbl_q2']), use_container_width=True, key="g_m_q2")
                    b4, b5, b6 = st.columns(3)
                    if b4.button(f"🟢 {p_m_q2}", key="bm_q2_p"): st.session_state.filtro_col_marca = "Cat_Filtro_Q2"; st.session_state.filtro_val_marca = "Promotor"; st.rerun()
                    if b5.button(f"🟡 {n_m_q2}", key="bm_q2_n"): st.session_state.filtro_col_marca = "Cat_Filtro_Q2"; st.session_state.filtro_val_marca = "Neutro"; st.rerun()
                    if b6.button(f"🔴 {d_m_q2}", key="bm_q2_d"): st.session_state.filtro_col_marca = "Cat_Filtro_Q2"; st.session_state.filtro_val_marca = "Detractor"; st.rerun()
                with c_mt:
                    st.metric("Muestra M.", t_m_q1)
                    if st.button("🔄 Ver Todos", key="btn_clear_m"): st.session_state.filtro_val_marca = "Todos"; st.rerun()
                
                # Segmentación y Gráficos de Proceso de Marca
                df_m_sub = df_m_base.copy()
                if st.session_state.filtro_val_marca != "Todos":
                    df_m_sub = df_m_sub[df_m_sub[st.session_state.filtro_col_marca] == st.session_state.filtro_val_marca]
                st.markdown(f"`Filtro Marca: {st.session_state.filtro_val_marca}`")
                
                tabs_m = st.tabs(["🤝 Ventas", "🚗 Test Drive", "📦 Entrega"])
                with tabs_m[0]:
                    v1, v2 = st.columns(2)
                    v1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q4']])[0], "Q4 - Cortesía Vendedor"), use_container_width=True, key="gm_q4")
                    v2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q5']])[0], "Q5 - Competencia Vendedor"), use_container_width=True, key="gm_q5")
                with tabs_m[1]:
                    t1, t2 = st.columns(2)
                    t1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub['Q7 - Satisfacción Test Drive'])[0], "Q7 - Score Test Drive"), use_container_width=True, key="gm_q7")
                    t2.plotly_chart(crear_grafico_torta(df_m_sub, MAPA_M['q6'], 'Q6 - Ofrecimiento TD'), use_container_width=True, key="pm_q6")
                with tabs_m[2]:
                    e1, e2 = st.columns(2)
                    e1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q8']])[0], "Q8 - Info Pre-entrega"), use_container_width=True, key="gm_q8")
                    e2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q11']])[0], "Q11 - Momento Entrega"), use_container_width=True, key="gm_q11")
                
                st.markdown("**💬 Verbalizaciones Marca:**")
                df_m_v = df_m_sub[["Fecha de ultimo contacto", "Nombre de cliente", MAPA_M['q3'], "Vendedor"]].copy().sort_values("Fecha de ultimo contacto", ascending=False)
                df_m_v["Fecha de ultimo contacto"] = df_m_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
                st.dataframe(df_m_v.rename(columns={MAPA_M['q3']: 'Comentario'}), use_container_width=True, hide_index=True, height=200)

            # --- COLUMNA DERECHA: ENCUESTAS INTERNAS ---
            with col_pantalla_interna:
                st.subheader("🎯 Encuestas Internas")
                
                val_i_q1, t_i_q1 = calcular_csi_directo_porcentaje(df_i_base[MAPA_I['q1']])
                serie_csi = limpiar_comas_a_numerico(df_i_base[MAPA_I['q1']]).dropna()
                p_i_q1 = (serie_csi >= 9.0).sum()
                n_i_q1 = ((serie_csi >= 7.0) & (serie_csi < 9.0)).sum()
                d_i_q1 = (serie_csi < 7.0).sum()
                
                nps_i_q2, p_i_q2, n_i_q2, d_i_q2, _ = calcular_nps_detallado(df_i_base[MAPA_I['q2']])
                
                c_i1, c_i2, c_it = st.columns([2, 2, 0.8])
                with c_i1:
                    st.plotly_chart(crear_gauge_moderno(val_i_q1, MAPA_I['lbl_q1']), use_container_width=True, key="g_i_q1")
                    bi1, bi2, bi3 = st.columns(3)
                    if bi1.button(f"🟢 {p_i_q1}", key="bi_q1_p"): st.session_state.filtro_col_interna = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_interna = "Promotor"; st.rerun()
                    if bi2.button(f"🟡 {n_i_q1}", key="bi_q1_n"): st.session_state.filtro_col_interna = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_interna = "Neutro"; st.rerun()
                    if bi3.button(f"🔴 {d_i_q1}", key="bi_q1_d"): st.session_state.filtro_col_interna = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_interna = "Detractor"; st.rerun()
                with c_i2:
                    st.plotly_chart(crear_gauge_moderno(nps_i_q2, MAPA_I['lbl_q2']), use_container_width=True, key="g_i_q2")
                    bi4, bi5, bi6 = st.columns(3)
                    if bi4.button(f"🟢 {p_i_q2}", key="bi_q2_p"): st.session_state.filtro_col_interna = "Cat_Filtro_Q2"; st.session_state.filtro_val_interna = "Promotor"; st.rerun()
                    if bi5.button(f"🟡 {n_i_q2}", key="bi_q2_n"): st.session_state.filtro_col_interna = "Cat_Filtro_Q2"; st.session_state.filtro_val_interna = "Neutro"; st.rerun()
                    if bi6.button(f"🔴 {d_i_q2}", key="bi_q2_d"): st.session_state.filtro_col_interna = "Cat_Filtro_Q2"; st.session_state.filtro_val_interna = "Detractor"; st.rerun()
                with c_it:
                    st.metric("Muestra Int.", t_i_q1)
                    if st.button("🔄 Ver Todos", key="btn_clear_i"): st.session_state.filtro_val_interna = "Todos"; st.rerun()
                
                # Segmentación y Gráficos de Proceso Internos
                df_i_sub = df_i_base.copy()
                if st.session_state.filtro_val_interna != "Todos":
                    df_i_sub = df_i_sub[df_i_sub[st.session_state.filtro_col_interna] == st.session_state.filtro_val_interna]
                st.markdown(f"`Filtro Interno: {st.session_state.filtro_val_interna}`")
                
                tabs_i = st.tabs(["🤝 Gestión Comercial", "📦 Procesos y Entrega", "📞 Contacto Post"])
                with tabs_i[0]:
                    vi1, vi2 = st.columns(2)
                    vi1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q4']])[0], "P2 - Cortesía Asesor"), use_container_width=True, key="gi_p2")
                    vi2.plotly_chart(crear_grafico_torta(df_i_sub, MAPA_I['q6'], 'P3 - Ofrecimiento TD'), use_container_width=True, key="pi_p3")
                with tabs_i[1]:
                    ei1, ei2 = st.columns(2)
                    ei1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q8']])[0], "P4 - Calidad Info Pre-entrega"), use_container_width=True, key="gi_p4")
                    ei2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q11']])[0], "P5 - Presentación 0km"), use_container_width=True, key="gi_p5")
                with tabs_i[2]:
                    pi1, pi2 = st.columns(2)
                    pi1.plotly_chart(crear_grafico_torta(df_i_sub, MAPA_I['q14'], 'P6 - Contacto Posterior'), use_container_width=True, key="pi_p6")
                    pi2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q15']])[0], "P7 - Sat. Contacto"), use_container_width=True, key="gi_p7")
                
                st.markdown("**💬 Verbalizaciones Internas:**")
                df_i_v = df_i_sub[["Fecha de ultimo contacto", "Nombre de cliente", MAPA_I['q3'], "Vendedor"]].copy().sort_values("Fecha de ultimo contacto", ascending=False)
                df_i_v["Fecha de ultimo contacto"] = df_i_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
                st.dataframe(df_i_v.rename(columns={MAPA_I['q3']: 'Comentario'}), use_container_width=True, hide_index=True, height=200)

        # ==========================================================
        # TAB 2: TABLA UNIFICADA DE ASESORES (CRUZA AMBAS FUENTES)
        # ==========================================================
        with tab_unificada:
            st.header("Ranking Comparativo por Asesor Comercial")
            
            resumen_master = []
            todos_vendedores = sorted(list(set(df_m_base["Vendedor"].dropna().unique()) | set(df_i_base["Vendedor"].dropna().unique())))
            
            for vend in todos_vendedores:
                data_m = df_m_base[df_m_base["Vendedor"] == vend]
                data_i = df_i_base[df_i_base["Vendedor"] == vend]
                
                n_m_q2, _, _, _, t_m = calcular_nps_detallado(data_m[MAPA_M['q2']]) if not data_m.empty else (0.0, 0, 0, 0, 0)
                n_i_q2, _, _, _, t_i = calcular_nps_detallado(data_i[MAPA_I['q2']]) if not data_i.empty else (0.0, 0, 0, 0, 0)
                
                resumen_master.append({
                    "Asesor Comercial": vend,
                    "NPS Rec. (MARCA)": round(n_m_q2, 1) if t_m > 0 else "Sin Datos",
                    "Muestra (MARCA)": t_m,
                    "NPS Rec. (INTERNA)": round(n_i_q2, 1) if t_i > 0 else "Sin Datos",
                    "Muestra (INTERNA)": t_i
                })
                
            df_master = pd.DataFrame(resumen_master)
            st.dataframe(df_master, use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 3: FICHA INDIVIDUAL POR ASESOR
        # ==========================================================
        with tab_individual:
            st.header("Evolución Histórica Cruzada por Asesor")
            vendedores_disponibles = sorted(list(set(df_m_base["Vendedor"].dropna().unique()) | set(df_i_base["Vendedor"].dropna().unique())))
            
            if vendedores_disponibles:
                vendedor_sel = st.selectbox("Seleccione el Asesor a evaluar:", options=vendedores_disponibles, key="sb_vendedor_unificado")
                
                col_hist1, col_hist2 = st.columns(2)
                
                with col_hist1:
                    st.subheader("Histórico Marca")
                    df_v_m = df_m_base[df_m_base["Vendedor"] == vendedor_sel]
                    if not df_v_m.empty:
                        v_q2, _, _, _, tv2 = calcular_nps_detallado(df_v_m[MAPA_M['q2']])
                        st.metric("NPS Recomendación Marca", f"{v_q2:.1f}%", f"Muestra: {tv2}")
                    else:
                        st.info("Sin datos de marca en este período.")
                        
                with col_hist2:
                    st.subheader("Histórico Interna")
                    df_v_i = df_i_base[df_i_base["Vendedor"] == vendedor_sel]
                    if not df_v_i.empty:
                        v_q2_i, _, _, _, tv2_i = calcular_nps_detallado(df_v_i[MAPA_I['q2']])
                        st.metric("NPS Recomendación Interna", f"{v_q2_i:.1f}%", f"Muestra: {tv2_i}")
                    else:
                        st.info("Sin datos internos en este período.")

except Exception as e:
    st.error(f"Error en la ejecución del Tablero Unificado Autociel: {e}")
