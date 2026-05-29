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
        title = {'text': f"<b>{titulo}</b>", 'font': {'size': 12, 'color': '#333'}},
        number = {'suffix': "%", 'font': {'size': 26}, 'valueformat': '.1f'},
        gauge = {
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': 94}
        }
    ))
    fig.update_layout(height=190, margin=dict(l=20, r=20, t=35, b=0), paper_bgcolor='rgba(0,0,0,0)')
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
        height=200, 
        margin=dict(l=10, r=10, t=40, b=10), 
        showlegend=False,
        annotations=[dict(
            text=f"<b>{pct_si:.1f}%</b><br><span style='font-size:10px;color:#666;font-weight:normal;'>{label_centro}</span>", 
            showarrow=False, 
            font=dict(size=18, color='#28a745' if label_centro == "Sí" else '#007bff')
        )]
    )
    return fig

# --- LÓGICA PRINCIPAL ---
try:
    # Inicialización de Filtros de Botones Independientes (para no mezclar clicks de Marca con Interna)
    if 'filtro_val_m' not in st.session_state: st.session_state.filtro_val_m = "Todos"
    if 'filtro_col_m' not in st.session_state: st.session_state.filtro_col_m = "Cat_Filtro_Dinamica"
    if 'filtro_val_i' not in st.session_state: st.session_state.filtro_val_i = "Todos"
    if 'filtro_col_i' not in st.session_state: st.session_state.filtro_col_i = "Cat_Filtro_Dinamica"

    # --- CARGA SIMULTÁNEA DE BASES ---
    df_m = load_data(URL_MARCA, "Encuestas de Marca")
    df_i = load_data(URL_INTERNA, "Encuestas Internas")
    
    if not df_m.empty and not df_i.empty:
        
        # MAPEO DE COLUMNAS (Mantenemos los dos intactos)
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
            'q14': 'contacto del concesionario posterior', 'q15': '7. ¿Cuán satisfecho se encuentra con el contacto posterior realizado por el concesionario?',
            'lbl_q1': 'CSI GENERAL (PROMEDIO %)', 'lbl_q2': '1. RECOMENDACIÓN (NPS)'
        }

        # Categorizaciones estructurales para clicks
        def generar_categorias(val):
            v = pd.to_numeric(val, errors='coerce')
            if pd.isna(v): return "Sin Datos"
            if v >= 9: return "Promotor"
            if v >= 7: return "Neutro"
            return "Detractor"

        df_m['Cat_Filtro_Dinamica'] = df_m[MAPA_M['q1']].apply(generar_categorias)
        df_m['Cat_Filtro_Q2'] = df_m[MAPA_M['q2']].apply(generar_categorias)
        
        df_i['Cat_Filtro_Dinamica'] = limpiar_comas_a_numerico(df_i[MAPA_I['q1']]).apply(generar_categorias)
        df_i['Cat_Filtro_Q2'] = limpiar_comas_a_numerico(df_i[MAPA_I['q2']]).apply(generar_categorias)

        # --- SIDEBAR (FILTROS GLOBALES UNIFICADOS) ---
        st.sidebar.header("Filtros Globales")
        df_m['Anio'] = df_m["Fecha de ultimo contacto"].dt.year
        df_m['Mes_Num'] = df_m["Fecha de ultimo contacto"].dt.month
        df_i['Anio'] = df_i["Fecha de ultimo contacto"].dt.year
        df_i['Mes_Num'] = df_i["Fecha de ultimo contacto"].dt.month
        
        # Universo de años y meses cruzados
        anios_combinados = sorted(list(set(df_m['Anio'].dropna().unique().astype(int)) | set(df_i['Anio'].dropna().unique().astype(int))), reverse=True)
        anio_sel = st.sidebar.selectbox("Año", options=anios_combinados if anios_combinados else [2026], key="sb_anio_unif")
        
        meses_n = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6: "Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        set_meses = set(df_m[df_m['Anio'] == anio_sel]['Mes_Num'].unique()) | set(df_i[df_i['Anio'] == anio_sel]['Mes_Num'].unique())
        meses_disp_nums = sorted(list(set_meses))
        meses_disp_nombres = [meses_n[m] for m in meses_disp_nums] if meses_disp_nums else ["Mayo"]
        
        meses_sel_nombres = st.sidebar.multiselect("Seleccione Mes(es)", options=meses_disp_nombres, default=meses_disp_nombres[-1:], key="sb_meses_unif")
        meses_sel_nums = [k for k, v in meses_n.items() if v in meses_sel_nombres]

        # Segmentación por tiempo
        df_m_time = df_m[(df_m["Anio"] == anio_sel) & (df_m["Mes_Num"].isin(meses_sel_nums))]
        df_i_time = df_i[(df_i["Anio"] == anio_sel) & (df_i["Mes_Num"].isin(meses_sel_nums))]

        # Universo unificado de marcas
        marcas_disponibles = sorted(list(set(df_m_time["MARCA"].dropna().unique()) | set(df_i_time["MARCA"].dropna().unique())))
        marcas = st.sidebar.multiselect("MARCA", options=marcas_disponibles, default=marcas_disponibles, key="sb_marcas_unif")

        # Universo unificado de canales
        canales_m = set(df_m_time[df_m_time["MARCA"].isin(marcas)]["Canal de Venta"].dropna().unique())
        canales_i = set(df_i_time[df_i_time["MARCA"].isin(marcas)]["Canal de Venta"].dropna().unique())
        canales_disponibles = sorted(list(canales_m | canales_i))
        canales = st.sidebar.multiselect("Canal de Venta", options=canales_disponibles, default=canales_disponibles, key="sb_canales_unif")

        # Filtros de bases base definitivos
        df_m_base = df_m_time[(df_m_time["MARCA"].isin(marcas)) & (df_m_time["Canal de Venta"].isin(canales))]
        df_i_base = df_i_time[(df_i_time["MARCA"].isin(marcas)) & (df_i_time["Canal de Venta"].isin(canales))]

        st.title("📊 Panel Integrado de Calidad - Autociel")
        
        tab_global, tab_unificada, tab_individual = st.tabs([
            "🏠 Monitor Global Comparativo", 
            "👥 Tabla Unificada de Asesores", 
            "👤 Ficha Individual por Asesor"
        ])

        # ==========================================================
        # TAB 1: MONITOR GLOBAL (Doble Columna en Pantalla)
        # ==========================================================
        with tab_global:
            st.header(f"Resultados en Paralelo: {', '.join(meses_sel_nombres)}")
            
            sc_marca, sc_interna = st.columns([1, 1])
            
            # --- PANEL DE MARCA (IZQUIERDA) ---
            with sc_marca:
                st.markdown("### 🏢 Datos de Origen: Encuestas de Marca")
                val_m_q1, p_m_q1, n_m_q1, d_m_q1, t_m_q1 = calcular_nps_detallado(df_m_base[MAPA_M['q1']])
                nps_m_q2, p_m_q2, n_m_q2, d_m_q2, _ = calcular_nps_detallado(df_m_base[MAPA_M['q2']])

                cm_q1, cm_q2, cm_tot = st.columns([2.2, 2.2, 0.8])
                with cm_q1:
                    st.plotly_chart(crear_gauge_moderno(val_m_q1, MAPA_M['lbl_q1']), use_container_width=True, key="gauge_m_q1")
                    col_m1, col_m2, col_m3 = st.columns(3)
                    if col_m1.button(f"🟢 {p_m_q1} Prom", key="bm_q1_p"): st.session_state.filtro_col_m = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_m = "Promotor"; st.rerun()
                    if col_m2.button(f"🟡 {n_m_q1} Neu", key="bm_q1_n"): st.session_state.filtro_col_m = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_m = "Neutro"; st.rerun()
                    if col_m3.button(f"🔴 {d_m_q1} Det", key="bm_q1_d"): st.session_state.filtro_col_m = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_m = "Detractor"; st.rerun()
                with cm_q2:
                    st.plotly_chart(crear_gauge_moderno(nps_m_q2, MAPA_M['lbl_q2']), use_container_width=True, key="gauge_m_q2")
                    col_m4, col_m5, col_m6 = st.columns(3)
                    if col_m4.button(f"🟢 {p_m_q2} Prom", key="bm_q2_p"): st.session_state.filtro_col_m = "Cat_Filtro_Q2"; st.session_state.filtro_val_m = "Promotor"; st.rerun()
                    if col_m5.button(f"🟡 {n_m_q2} Neu", key="bm_q2_n"): st.session_state.filtro_col_m = "Cat_Filtro_Q2"; st.session_state.filtro_val_m = "Neutro"; st.rerun()
                    if col_m6.button(f"🔴 {d_m_q2} Det", key="bm_q2_d"): st.session_state.filtro_col_m = "Cat_Filtro_Q2"; st.session_state.filtro_val_m = "Detractor"; st.rerun()
                with cm_tot:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Muestra", t_m_q1)
                    if st.button("🔄 Ver Todos", key="btn_clear_m"): st.session_state.filtro_val_m = "Todos"; st.rerun()

                # Cascadas Internas de Marca
                df_m_sub = df_m_base.copy()
                if st.session_state.filtro_val_m != "Todos":
                    df_m_sub = df_m_sub[df_m_sub[st.session_state.filtro_col_m] == st.session_state.filtro_val_m]
                
                st.markdown(f"**Segmentación actual Marca:** `{st.session_state.filtro_val_m}`")
                stabs_m = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
                with stabs_m[0]:
                    v1, v2 = st.columns(2)
                    v1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q4']])[0], "Q4 - Cortesía y Amabilidad"), use_container_width=True, key="g_m_q4")
                    v2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q5']])[0], "Q5 - Competencia Vendedor"), use_container_width=True, key="g_m_q5")
                with stabs_m[1]:
                    ct1, ct2 = st.columns(2)
                    ct1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub['Q7 - Satisfacción Test Drive'])[0], "Q7 - Sat. Test Drive"), use_container_width=True, key="g_m_q7")
                    ct2.plotly_chart(crear_grafico_torta(df_m_sub, MAPA_M['q6'], 'Q6 - Ofrecimiento Test Drive'), use_container_width=True, key="p_m_q6")
                with stabs_m[2]:
                    cf1, cf2 = st.columns(2)
                    cf1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub['Q10 - Satisfacción Financiación utilizada'])[0], "Q10 - Sat. Financiación"), use_container_width=True, key="g_m_q10")
                    cf2.plotly_chart(crear_grafico_torta(df_m_sub, 'Q9 - Financiación utilizada', 'Mix Ventas Financiadas'), use_container_width=True, key="p_m_q9")
                with stabs_m[3]:
                    ce1, ce2 = st.columns(2)
                    ce1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q8']])[0], "Q8 - Info Pre-entrega"), use_container_width=True, key="g_m_q8")
                    ce2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_m_sub[MAPA_M['q11']])[0], "Q11 - Momento de la entrega"), use_container_width=True, key="g_m_q11")
                    st.plotly_chart(crear_grafico_torta(df_m_sub, MAPA_M['q14'], 'Q14 - Contactado Posterior'), use_container_width=True, key="p_m_q14")

                st.markdown("##### 💬 Verbalizaciones del Cliente (Marca)")
                df_m_v = df_m_sub[["Fecha de ultimo contacto", "Nombre de cliente", MAPA_M['q3'], "Vendedor"]].copy().sort_values("Fecha de ultimo contacto", ascending=False)
                df_m_v["Fecha de ultimo contacto"] = df_m_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
                st.dataframe(df_m_v.rename(columns={MAPA_M['q3']: 'Comentario Textual'}), use_container_width=True, hide_index=True, height=220)

            # --- PANEL INTERNO (DERECHA) ---
            with sc_interna:
                st.markdown("### 🎯 Datos de Origen: Encuestas Internas")
                val_i_q1, t_i_q1 = calcular_csi_directo_porcentaje(df_i_base[MAPA_I['q1']])
                serie_csi = limpiar_comas_a_numerico(df_i_base[MAPA_I['q1']]).dropna()
                p_i_q1 = (serie_csi >= 9.0).sum()
                n_i_q1 = ((serie_csi >= 7.0) & (serie_csi < 9.0)).sum()
                d_i_q1 = (serie_csi < 7.0).sum()
                nps_i_q2, p_i_q2, n_i_q2, d_i_q2, _ = calcular_nps_detallado(df_i_base[MAPA_I['q2']])

                ci_q1, ci_q2, ci_tot = st.columns([2.2, 2.2, 0.8])
                with ci_q1:
                    st.plotly_chart(crear_gauge_moderno(val_i_q1, MAPA_I['lbl_q1']), use_container_width=True, key="gauge_i_q1")
                    col_i1, col_i2, col_i3 = st.columns(3)
                    if col_i1.button(f"🟢 {p_i_q1} Prom", key="bi_q1_p"): st.session_state.filtro_col_i = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_i = "Promotor"; st.rerun()
                    if col_i2.button(f"🟡 {n_i_q1} Neu", key="bi_q1_n"): st.session_state.filtro_col_i = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_i = "Neutro"; st.rerun()
                    if col_i3.button(f"🔴 {d_i_q1} Det", key="bi_q1_d"): st.session_state.filtro_col_i = "Cat_Filtro_Dinamica"; st.session_state.filtro_val_i = "Detractor"; st.rerun()
                with ci_q2:
                    st.plotly_chart(crear_gauge_moderno(nps_i_q2, MAPA_I['lbl_q2']), use_container_width=True, key="gauge_i_q2")
                    col_i4, col_i5, col_i6 = st.columns(3)
                    if col_i4.button(f"🟢 {p_i_q2} Prom", key="bi_q2_p"): st.session_state.filtro_col_i = "Cat_Filtro_Q2"; st.session_state.filtro_val_i = "Promotor"; st.rerun()
                    if col_i5.button(f"🟡 {n_i_q2} Neu", key="bi_q2_n"): st.session_state.filtro_col_i = "Cat_Filtro_Q2"; st.session_state.filtro_val_i = "Neutro"; st.rerun()
                    if col_i6.button(f"🔴 {d_i_q2} Det", key="bi_q2_d"): st.session_state.filtro_col_i = "Cat_Filtro_Q2"; st.session_state.filtro_val_i = "Detractor"; st.rerun()
                with ci_tot:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.metric("Muestra", t_i_q1)
                    if st.button("🔄 Ver Todos", key="btn_clear_i"): st.session_state.filtro_val_i = "Todos"; st.rerun()

                # Cascadas Internas de Internas
                df_i_sub = df_i_base.copy()
                if st.session_state.filtro_val_i != "Todos":
                    df_i_sub = df_i_sub[df_i_sub[st.session_state.filtro_col_i] == st.session_state.filtro_val_i]
                
                st.markdown(f"**Segmentación actual Interna:** `{st.session_state.filtro_val_i}`")
                stabs_i = st.tabs(["🤝 Gestión Comercial", "📦 Procesos y Entrega", "📞 Contacto posterior"])
                with stabs_i[0]:
                    vi1, vi2 = st.columns(2)
                    vi1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q4']])[0], "Preg. 2 - Cortesía y Amabilidad"), use_container_width=True, key="g_i_p2")
                    vi2.plotly_chart(crear_grafico_torta(df_i_sub, MAPA_I['q6'], 'Preg. 3 - Ofrecimiento de Test Drive'), use_container_width=True, key="p_i_p3")
                with stabs_i[1]:
                    ei1, ei2 = st.columns(2)
                    ei1.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q8']])[0], "Preg. 4 - Calidad de Info Pre-entrega"), use_container_width=True, key="g_i_p4")
                    ei2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q11']])[0], "Preg. 5 - Presentación del 0KM"), use_container_width=True, key="g_i_p5")
                with stabs_i[2]:
                    pi1, pi2 = st.columns(2)
                    pi1.plotly_chart(crear_grafico_torta(df_i_sub, MAPA_I['q14'], 'Preg. 6 - Recepción Contacto'), use_container_width=True, key="p_i_p6")
                    pi2.plotly_chart(crear_gauge_moderno(calcular_csi_directo_porcentaje(df_i_sub[MAPA_I['q15']])[0], "Preg. 7 - Sat. Contacto Posterior"), use_container_width=True, key="g_i_p7")

                st.markdown("##### 💬 Verbalizaciones del Cliente (Internas)")
                df_i_v = df_i_sub[["Fecha de ultimo contacto", "Nombre de cliente", MAPA_I['q3'], "Vendedor"]].copy().sort_values("Fecha de ultimo contacto", ascending=False)
                df_i_v["Fecha de ultimo contacto"] = df_i_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
                st.dataframe(df_i_v.rename(columns={MAPA_I['q3']: 'Comentario Textual'}), use_container_width=True, hide_index=True, height=220)

        # ==========================================================
        # TAB 2: TABLA UNIFICADA DE ASESORES (CRUZA AMBAS FUENTES)
        # ==========================================================
        with tab_unificada:
            st.header("Ranking de Performance Comercial Integrado")
            
            # Unificamos la lista completa de vendedores presentes en cualquiera de las dos bases
            vendedores_unificados = sorted(list(set(df_m_base["Vendedor"].dropna().unique()) | set(df_i_base["Vendedor"].dropna().unique())))
            
            if vendedores_unificados:
                resumen_master = []
                for vend in vendedores_unificados:
                    data_m = df_m_base[df_m_base["Vendedor"] == vend]
                    data_i = df_i_base[df_i_base["Vendedor"] == vend]
                    
                    # Cálculos de Marca si existen datos para el asesor
                    if not data_m.empty:
                        nm_q2, pm_q2, _, dm_q2, tm_q2 = calcular_nps_detallado(data_m[MAPA_M['q2']])
                        target_m = calcular_faltante_94(pm_q2, dm_q2, tm_q2)
                    else:
                        nm_q2, target_m, tm_q2 = 0.0, "Sin registros", 0
                        
                    # Cálculos de Interna si existen datos para el asesor
                    if not data_i.empty:
                        ni_q2, pi_q2, _, di_q2, ti_q2 = calcular_nps_detallado(data_i[MAPA_I['q2']])
                        target_i = calcular_faltante_94(pi_q2, di_q2, ti_q2)
                    else:
                        ni_q2, target_i, ti_q2 = 0.0, "Sin registros", 0
                    
                    resumen_master.append({
                        "Asesor Comercial": vend,
                        "NPS Rec. (MARCA)": round(nm_q2, 1) if tm_q2 > 0 else "Sin Datos",
                        "Faltante Obj. M (94%)": target_m,
                        "Muestra M": tm_q2,
                        "NPS Rec. (INTERNA)": round(ni_q2, 1) if ti_q2 > 0 else "Sin Datos",
                        "Faltante Obj. I (94%)": target_i,
                        "Muestra I": ti_q2
                    })
                
                df_master = pd.DataFrame(resumen_master).sort_values("Muestra M", ascending=False)
                
                def color_celda_nps(val):
                    try:
                        v = float(val)
                        if v >= 94: return 'background-color: #d4edda; color: #155724; font-weight: bold'
                        if v >= 90: return 'background-color: #fff3cd; color: #856404; font-weight: bold'
                        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                    except:
                        return ''

                df_styled = df_master.style.map(color_celda_nps, subset=["NPS Rec. (MARCA)", "NPS Rec. (INTERNA)"])\
                                           .map(lambda x: 'color: #721c24; font-weight: bold' if '🚨' in str(x) else 'color: #155724', subset=['Faltante Obj. M (94%)', 'Faltante Obj. I (94%)'])
                
                st.dataframe(df_styled, use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 3: FICHA INDIVIDUAL POR ASESOR (CRUZADO HISTÓRICO)
        # ==========================================================
        with tab_individual:
            st.header("Evolución Histórica por Asesor (Comparativa de Fuentes)")
            
            vendedores_disponibles = sorted(list(set(df_m_base["Vendedor"].dropna().unique()) | set(df_i_base["Vendedor"].dropna().unique())))
            if vendedores_disponibles:
                vendedor_sel = st.selectbox("Seleccione el Asesor a evaluar:", options=vendedores_disponibles, key="sb_vendedor_unif")
                
                st.markdown(f"### Desempeño de: **{vendedor_sel}**")
                
                col_ficha_m, col_ficha_i = st.columns(2)
                
                # --- EVOLUCIÓN HISTÓRICA MARCA ---
                with col_ficha_m:
                    st.markdown("#### 🏢 Histórico de Marca")
                    df_vend_m = df_m_base[df_m_base["Vendedor"] == vendedor_sel]
                    
                    if not df_vend_m.empty:
                        df_vend_full_m = df_m[(df_m["Vendedor"] == vendedor_sel) & (df_m["MARCA"].isin(marcas)) & (df_m["Canal de Venta"].isin(canales))].copy()
                        df_vend_full_m["Periodo"] = df_vend_full_m["Fecha de ultimo contacto"].dt.to_period("M")
                        
                        resumen_mensual_m = []
                        for per, data_m in df_vend_full_m.groupby("Periodo"):
                            n_m, _, _, _, _ = calcular_nps_detallado(data_m[MAPA_M['q2']])
                            resumen_mensual_m.append({"Periodo_Str": str(per), "Periodo": per, "NPS": n_m})
                        
                        df_ev_m = pd.DataFrame(resumen_mensual_m).sort_values("Periodo")
                        vm_q2, _, _, _, tv2 = calcular_nps_detallado(df_vend_m[MAPA_M['q2']])
                        
                        st.metric("NPS Recomendación Actual (Marca)", f"{vm_q2:.1f}%", f"Muestra: {tv2} encuestas")
                        
                        if not df_ev_m.empty:
                            fig_m = px.line(df_ev_m, x="Periodo_Str", y="NPS", text=df_ev_m["NPS"].round(1).astype(str) + "%", labels={"Periodo_Str": "Mes", "NPS": "NPS Marca %"}, markers=True)
                            fig_m.add_hline(y=94, line_dash="dash", line_color="green", annotation_text="Objetivo (94%)")
                            fig_m.update_traces(textposition="top center", line=dict(color='#28a745', width=3))
                            fig_m.update_layout(yaxis=dict(range=[-10, 110]), height=240, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_m, use_container_width=True, key="linea_ev_marca")
                    else:
                        st.info("Sin registros en la base de Marca para este asesor.")

                # --- EVOLUCIÓN HISTÓRICA INTERNA ---
                with col_ficha_i:
                    st.markdown("#### 🎯 Histórico Interno")
                    df_vend_i = df_i_base[df_i_base["Vendedor"] == vendedor_sel]
                    
                    if not df_vend_i.empty:
                        df_vend_full_i = df_i[(df_i["Vendedor"] == vendedor_sel) & (df_i["MARCA"].isin(marcas)) & (df_i["Canal de Venta"].isin(canales))].copy()
                        df_vend_full_i["Periodo"] = df_vend_full_i["Fecha de ultimo contacto"].dt.to_period("M")
                        
                        resumen_mensual_i = []
                        for per, data_m in df_vend_full_i.groupby("Periodo"):
                            n_m, _, _, _, _ = calcular_nps_detallado(data_m[MAPA_I['q2']])
                            resumen_mensual_i.append({"Periodo_Str": str(per), "Periodo": per, "NPS": n_m})
                        
                        df_ev_i = pd.DataFrame(resumen_mensual_i).sort_values("Periodo")
                        vi_q2, _, _, _, tv2_i = calcular_nps_detallado(df_vend_i[MAPA_I['q2']])
                        
                        st.metric("NPS Recomendación Actual (Interno)", f"{vi_q2:.1f}%", f"Muestra: {tv2_i} encuestas")
                        
                        if not df_ev_i.empty:
                            fig_i = px.line(df_ev_i, x="Periodo_Str", y="NPS", text=df_ev_i["NPS"].round(1).astype(str) + "%", labels={"Periodo_Str": "Mes", "NPS": "NPS Interno %"}, markers=True)
                            fig_i.add_hline(y=94, line_dash="dash", line_color="green", annotation_text="Objetivo (94%)")
                            fig_i.update_traces(textposition="top center", line=dict(color='#007bff', width=3))
                            fig_i.update_layout(yaxis=dict(range=[-10, 110]), height=240, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_i, use_container_width=True, key="linea_ev_interna")
                    else:
                        st.info("Sin registros en la base Interna para este asesor.")

except Exception as e:
    st.error(f"Error en la ejecución del Tablero Integrado: {e}")
