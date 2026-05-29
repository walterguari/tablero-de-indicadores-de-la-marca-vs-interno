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
@st.cache_data(ttl=600)
def load_data(url, tipo_base):
    try:
        csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=").replace("/edit?gid=", "/export?format=csv&gid=")
        df = pd.read_csv(csv_url)
        
        # Normalización y mapeo estructural según el origen de datos
        if tipo_base == "Encuestas de Marca":
            df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
        else:
            # Mapeo idéntico para la base Interna respetando las mayúsculas de tu archivo
            df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de último contacto"], dayfirst=True, errors='coerce')
            df["MARCA"] = df["MARCA"]
            df["Canal de Venta"] = df["CANAL DE VENTA"]
            df["Vendedor"] = df["VENDEDOR"]
            
            # Forzar la columna de cliente según lo visto en la imagen
            if "Cliente" in df.columns:
                df["Nombre de cliente"] = df["Cliente"]
            elif "Nombre de cliente" not in df.columns:
                df["Nombre de cliente"] = "Cliente Autociel"
                
        return df
    except Exception as e:
        st.error(f"Error al cargar datos ({tipo_base}): {e}")
        return pd.DataFrame()

def calcular_nps_detallado(serie):
    if serie is None or serie.empty: return 0, 0, 0, 0, 0
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    total = len(serie)
    if total == 0: return 0, 0, 0, 0, 0
    promotores = (serie >= 9).sum()
    neutros = ((serie >= 7) & (serie <= 8)).sum()
    detractores = (serie <= 6).sum()
    nps = ((promotores - detractores) / total) * 100
    return nps, promotores, neutros, detractores, total

def calcular_promedio(serie):
    if serie is None or serie.empty: return 0.0, 0
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    if len(serie) == 0: return 0.0, 0
    return serie.mean(), len(serie)

def calcular_faltante_94(promotores, detractores, total):
    if total == 0: return "Sin datos"
    nps_actual = ((promotores - detractores) / total) * 100
    if nps_actual >= 94: return "✅ Objetivo"
    x = (0.94 * total + detractores - promotores) / (1 - 0.94)
    return f"🚨 Faltan {math.ceil(x)}"

def get_bar_color(val, es_promedio=False):
    limite_sup = 9.4 if es_promedio else 94
    limite_med = 9.0 if es_promedio else 90
    if val >= limite_sup: return '#28a745'
    if val >= limite_med: return '#ffc107'
    return '#dc3545'

def crear_gauge_moderno(valor, titulo, es_promedio=False):
    color_viva = get_bar_color(valor, es_promedio)
    max_val = 10 if es_promedio else 100
    sufijo = "" if es_promedio else "%"
    val_objetivo = 9.4 if es_promedio else 94
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = valor,
        title = {'text': f"<b>{titulo}</b>", 'font': {'size': 16, 'color': '#333'}},
        number = {'suffix': sufijo, 'font': {'size': 38}, 'valueformat': '.2f' if es_promedio else '.1f'},
        gauge = {
            'axis': {'range': [0, max_val], 'visible': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': val_objetivo}
        }
    ))
    fig.update_layout(height=220, margin=dict(l=30, r=30, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def crear_grafico_torta(df, columna, titulo):
    if columna not in df.columns: return go.Figure()
    conteo = df[columna].value_counts().reset_index()
    conteo.columns = [columna, 'Cantidad']
    fig = px.pie(conteo, values='Cantidad', names=columna, title=titulo, hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label+value')
    fig.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10))
    return fig

# --- LÓGICA PRINCIPAL ---
try:
    st.sidebar.header("Origen de Datos")
    base_seleccionada = st.sidebar.radio(
        "Seleccione Tipo de Encuesta:",
        options=["Encuestas de Marca", "Encuestas Internas"]
    )
    
    sheet_url = URL_MARCA if base_seleccionada == "Encuestas de Marca" else URL_INTERNA
    df = load_data(sheet_url, base_seleccionada)
    
    if not df.empty:
        # --- MAPEO DINÁMICO DE COLUMNAS EXACTO ---
        if base_seleccionada == "Encuestas de Marca":
            MAPA = {
                'q1': 'Q1 - Satisfacción general',
                'q2': 'Q2 - Recomendación - Concesionario',
                'q3': 'Q3 - Verbalización',
                'q4': 'Q4 - Cortesía y amabilidad',
                'q5': 'Q5 - Competencia Vendedor',
                'q6': 'Q6 - Ofrecimiento Test Drive',
                'q8': 'Q8 - Satisfacción información entre compra y entrega',
                'q11': 'Q11 - Satisfacción Momento de la entrega',
                'q14': 'Q14 - Contactado',
                'q15': 'Q15 - Satisfacción con el Contacto',
                'lbl_q1': 'Q1 - SATISFACCIÓN (NPS)',
                'lbl_q2': 'Q2 - RECOMENDACIÓN (NPS)'
            }
        else:
            MAPA = {
                'q1': 'CSI', 
                'q2': '1. Basándose en su experiencia de compra, ¿Recomendaría el Concesionario a familiares y amigos?',
                'q3': 'COMENTARIO DEL CLIENTE',
                'q4': '2. ¿Cómo califica la cortesía y amabilidad del Vendedor / Asesor Comercial?',
                'q5': None,
                'q6': '3. ¿Le han ofrecido una prueba de manejo?',
                'q8': '4. ¿Cómo califica la información facilitada entre la compra y la entrega de su vehículo nuevo?',
                'q11': '5. ¿Cómo califica la presentación de su 0KM al momento de la entrega?',
                'q14': '6. ¿Recibió un contacto del concesionario posterior a la entrega de su vehículo?',
                'q15': '7. ¿Cuán satisfecho se encuentra con el contacto posterior realizado por el concesionario?',
                'lbl_q1': 'CSI GENERAL (PROMEDIO)',
                'lbl_q2': '1. RECOMENDACIÓN (NPS)'
            }

        def categorizar_rapido(val):
            v = pd.to_numeric(val, errors='coerce')
            if v >= 9: return "Promotor"
            if v >= 7: return "Neutro"
            return "Detractor"

        df['Cat_Q1_Dinamica'] = df[MAPA['q1']].apply(categorizar_rapido)
        df['Cat_Q2_Dinamica'] = df[MAPA['q2']].apply(categorizar_rapido)

        # --- FILTROS GLOBALES TEMPORALES Y DE SEGMENTO ---
        st.sidebar.markdown("---")
        st.sidebar.header("Filtros Globales")
        df['Anio'] = df["Fecha de ultimo contacto"].dt.year
        df['Mes_Num'] = df["Fecha de ultimo contacto"].dt.month
        
        anios_disponibles = sorted(df['Anio'].dropna().unique().astype(int), reverse=True)
        anio_sel = st.sidebar.selectbox("Año", options=anios_disponibles if anios_disponibles else [2026])
        
        meses_n = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6: "Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
        meses_disp_nums = sorted(df[df['Anio'] == anio_sel]['Mes_Num'].unique())
        meses_disp_nombres = [meses_n[m] for m in meses_disp_nums] if meses_disp_nums else ["Mayo"]
        
        meses_sel_nombres = st.sidebar.multiselect("Seleccione Mes(es)", options=meses_disp_nombres, default=meses_disp_nombres[-1:])
        meses_sel_nums = [k for k, v in meses_n.items() if v in meses_sel_nombres]

        df_time = df[(df["Anio"] == anio_sel) & (df["Mes_Num"].isin(meses_sel_nums))]

        marcas_disponibles = sorted(df_time["MARCA"].dropna().unique())
        marcas = st.sidebar.multiselect("MARCA", options=marcas_disponibles, default=marcas_disponibles)

        canales_disponibles = sorted(df_time[df_time["MARCA"].isin(marcas)]["Canal de Venta"].dropna().unique())
        canales = st.sidebar.multiselect("Canal de Venta", options=canales_disponibles, default=canales_disponibles)

        df_base = df_time[(df_time["MARCA"].isin(marcas)) & (df_time["Canal de Venta"].isin(canales))]

        st.title(f"📊 Control de Calidad Autociel - {base_seleccionada}")
        
        tab_global, tab_unificada, tab_individual = st.tabs([
            "🏠 Monitor Global", 
            "👥 Tabla Unificada de Asesores", 
            "👤 Ficha Individual por Asesor"
        ])

        if 'filtro_col' not in st.session_state: st.session_state.filtro_col = "Cat_Q2_Dinamica"
        if 'filtro_val' not in st.session_state: st.session_state.filtro_val = "Todos"

        # ==========================================================
        # TAB 1: MONITOR GLOBAL
        # ==========================================================
        with tab_global:
            st.header(f"Resultados Consolidados: {', '.join(meses_sel_nombres)}")
            
            # Condicional para calcular Q1 (NPS) o CSI (Promedio) según la base activa
            if base_seleccionada == "Encuestas de Marca":
                val_q1, p_q1, n_q1, d_q1, t_q1 = calcular_nps_detallado(df_base[MAPA['q1']])
                es_prom = False
            else:
                val_q1, t_q1 = calcular_promedio(df_base[MAPA['q1']])
                p_q1, n_q1, d_q1 = 0, 0, 0
                es_prom = True
                
            nps_q2, p_q2, n_q2, d_q2, _ = calcular_nps_detallado(df_base[MAPA['q2']])

            c_q1, c_q2, c_tot = st.columns([2.2, 2.2, 0.6])
            with c_q1:
                st.plotly_chart(crear_gauge_moderno(val_q1, MAPA['lbl_q1'], es_promedio=es_prom), use_container_width=True, key="g_q1_autociel_v3")
                if not es_prom:
                    col_b1, col_b2, col_b3 = st.columns(3)
                    if col_b1.button(f"🟢 {p_q1} Prom", key="btn_q1_p3"): 
                        st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q1_Dinamica", "Promotor"; st.rerun()
                    if col_b2.button(f"🟡 {n_q1} Neu", key="btn_q1_n3"): 
                        st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q1_Dinamica", "Neutro"; st.rerun()
                    if col_b3.button(f"🔴 {d_q1} Det", key="btn_q1_d3"): 
                        st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q1_Dinamica", "Detractor"; st.rerun()
            with c_q2:
                st.plotly_chart(crear_gauge_moderno(nps_q2, MAPA['lbl_q2']), use_container_width=True, key="g_q2_autociel_v3")
                col_b4, col_b5, col_b6 = st.columns(3)
                if col_b4.button(f"🟢 {p_q2} Prom", key="btn_q2_p3"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q2_Dinamica", "Promotor"; st.rerun()
                if col_b5.button(f"🟡 {n_q2} Neu", key="btn_q2_n3"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q2_Dinamica", "Neutro"; st.rerun()
                if col_b6.button(f"🔴 {d_q2} Det", key="btn_q2_d3"): 
                    st.session_state.filtro_col, st.session_state.filtro_val = "Cat_Q2_Dinamica", "Detractor"; st.rerun()
            with c_tot:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.metric("Respuestas", t_q1)
                if st.button("🔄 Ver\nTodos", key="clear_filtros_autociel_v3"): 
                    st.session_state.filtro_val = "Todos"
                    st.rerun()

            st.markdown("---")
            
            if base_seleccionada == "Encuestas de Marca":
                stabs = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
                with stabs[0]:
                    v1, v2 = st.columns(2)
                    v1.metric("Q4 - Cortesía y Amabilidad", f"{calcular_nps_detallado(df_base[MAPA['q4']])[0]:.1f}%")
                    v2.metric("Q5 - Competencia Vendedor", f"{calcular_nps_detallado(df_base[MAPA['q5']])[0]:.1f}%")
                with stabs[1]:
                    ct1, ct2 = st.columns(2)
                    ct1.metric("Q7 - Satisfacción Test Drive", f"{calcular_nps_detallado(df_base['Q7 - Satisfacción Test Drive'])[0]:.1f}%")
                    st.plotly_chart(crear_grafico_torta(df_base, MAPA['q6'], 'Q6 - Ofrecimiento Test Drive'), use_container_width=True, key="t_td_m3")
                with stabs[2]:
                    cf1, cf2 = st.columns(2)
                    cf1.metric("Q10 - Satisfacción Financiación", f"{calcular_nps_detallado(df_base['Q10 - Satisfacción Financiación utilizada'])[0]:.1f}%")
                    st.plotly_chart(crear_grafico_torta(df_base, 'Q9 - Financiación utilizada', 'Mix Ventas Financiadas'), use_container_width=True, key="t_fin_m3")
                with stabs[3]:
                    ce1, ce2 = st.columns(2)
                    ce1.metric("Q8 - Info Pre-entrega", f"{calcular_nps_detallado(df_base[MAPA['q8']])[0]:.1f}%")
                    ce2.metric("Q11 - Momento de la entrega", f"{calcular_nps_detallado(df_base[MAPA['q11']])[0]:.1f}%")
            else:
                stabs_int = st.tabs(["🤝 Gestión Comercial", "📦 Procesos y Entrega", "📞 Seguimiento Postventa"])
                with stabs_int[0]:
                    v1, v2 = st.columns(2)
                    v1.metric("Preg. 2 - Cortesía y Amabilidad del Asesor", f"{calcular_nps_detallado(df_base[MAPA['q4']])[0]:.1f}%")
                    st.plotly_chart(crear_grafico_torta(df_base, MAPA['q6'], 'Preg. 3 - Ofrecimiento de Test Drive'), use_container_width=True, key="t_td_i3")
                with stabs_int[1]:
                    e1, e2 = st.columns(2)
                    e1.metric("Preg. 4 - Calidad de Info Pre-entrega", f"{calcular_nps_detallado(df_base[MAPA['q8']])[0]:.1f}%")
                    e2.metric("Preg. 5 - Presentación y Estado del 0KM", f"{calcular_nps_detallado(df_base[MAPA['q11']])[0]:.1f}%")
                with stabs_int[2]:
                    p1, p2 = st.columns(2)
                    st.plotly_chart(crear_grafico_torta(df_base, MAPA['q14'], 'Preg. 6 - Recepción de Contacto Post-Entrega'), use_container_width=True, key="t_post_i3")
                    p2.metric("Preg. 7 - Satisfacción con la llamada/whatsapp", f"{calcular_nps_detallado(df_base[MAPA['q15']])[0]:.1f}%")

            st.markdown("---")
            label_f = "Todos los registros" if st.session_state.filtro_val == "Todos" else f"Filtro activo: {st.session_state.filtro_val}"
            st.subheader(f"💬 Comentarios y Verbalizaciones del Cliente ({label_f})")
            
            df_v = df_base[["Fecha de ultimo contacto", "Nombre de cliente", MAPA['q3'], "Vendedor", "Cat_Q1_Dinamica", "Cat_Q2_Dinamica"]].copy()
            if st.session_state.filtro_val != "Todos":
                df_v = df_v[df_v[st.session_state.filtro_col] == st.session_state.filtro_val]
            
            df_v = df_v.sort_values("Fecha de ultimo contacto", ascending=False)
            df_v["Fecha de ultimo contacto"] = df_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_v[["Fecha de ultimo contacto", "Nombre de cliente", MAPA['q3'], "Vendedor"]].rename(columns={MAPA['q3']: 'Comentario textual / Concatenado'}), use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 2: TABLA UNIFICADA DE ASESORES
        # ==========================================================
        with tab_unificada:
            st.header("Ranking de Performance por Asesor Comercial")
            st.markdown("Hacé clic en cualquier cabecera para ordenar la lista según el indicador deseado.")
            
            if not df_base.empty:
                resumen_master = []
                for vend, data in df_base.groupby("Vendedor"):
                    n_q2, p_q2, _, d_q2, t_q2 = calcular_nps_detallado(data[MAPA['q2']])
                    n_q4, _, _, _, _ = calcular_nps_detallado(data[MAPA['q4']])
                    n_q8, _, _, _, _ = calcular_nps_detallado(data[MAPA['q8']])
                    
                    resumen_master.append({
                        "Asesor Comercial": vend,
                        "NPS Recomendación": round(n_q2, 1),
                        "Faltante Obj. 94%": calcular_faltante_94(p_q2, d_q2, t_q2),
                        "NPS Cortesía y Trato": round(n_q4, 1),
                        "NPS Info Pre-Entrega": round(n_q8, 1),
                        "Muestra (Encuestas)": t_q2
                    })
                
                df_master = pd.DataFrame(resumen_master).sort_values("NPS Recomendación", ascending=False)
                
                def color_celda_nps(val):
                    try:
                        v = float(val)
                        if v >= 94: return 'background-color: #d4edda; color: #155724; font-weight: bold'
                        if v >= 90: return 'background-color: #fff3cd; color: #856404; font-weight: bold'
                        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                    except:
                        return ''

                df_styled = df_master.style.map(color_celda_nps, subset=["NPS Recomendación", "NPS Cortesía y Trato", "NPS Info Pre-Entrega"])\
                                           .map(lambda x: 'color: #721c24; font-weight: bold' if '🚨' in str(x) else 'color: #155724', subset=['Faltante Obj. 94%'])
                
                st.dataframe(df_styled, use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 3: FICHA INDIVIDUAL POR ASESOR
        # ==========================================================
        with tab_individual:
            st.header("Evolución Histórica por Asesor")
            
            vendedores_disponibles = sorted(df_base["Vendedor"].dropna().unique())
            if vendedores_disponibles:
                vendedor_sel = st.selectbox("Seleccione el Asesor a evaluar:", options=vendedores_disponibles, key="sb_vend_ind3")
                df_vend = df_base[df_base["Vendedor"] == vendedor_sel]
                
                df_vend_full = df[(df["Vendedor"] == vendedor_sel) & (df["MARCA"].isin(marcas)) & (df["Canal de Venta"].isin(canales))].copy()
                df_vend_full["Periodo"] = df_vend_full["Fecha de ultimo contacto"].dt.to_period("M")
                
                resumen_mensual = []
                for per, data_m in df_vend_full.groupby("Periodo"):
                    n_m, _, _, _, _ = calcular_nps_detallado(data_m[MAPA['q2']])
                    resumen_mensual.append({"Periodo_Str": str(per), "Periodo": per, "NPS": n_m})
                
                df_evolucion = pd.DataFrame(resumen_mensual).sort_values("Periodo")
                
                st.markdown(f"### Desempeño de: **{vendedor_sel}**")
                
                v_q2, pv2, _, dv2, tv2 = calcular_nps_detallado(df_vend[MAPA['q2']])
                v_q4, _, _, _, _ = calcular_nps_detallado(df_vend[MAPA['q4']])
                v_q8, _, _, _, _ = calcular_nps_detallado(df_vend[MAPA['q8']])
                
                alerta_q2 = ""
                if len(df_evolucion) >= 2:
                    ultimo_nps = df_evolucion.iloc[-1]["NPS"]
                    anterior_nps = df_evolucion.iloc[-2]["NPS"]
                    if ultimo_nps > anterior_nps:
                        alerta_q2 = f"⬆️ (+{ultimo_nps - anterior_nps:.1f}% vs mes ant.)"
                    elif ultimo_nps < anterior_nps:
                        alerta_q2 = f"⬇️ ({ultimo_nps - anterior_nps:.1f}% vs mes ant.)"
                    else:
                        alerta_q2 = "➡️ (Sin cambios)"

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("NPS Recomendación Actual", f"{v_q2:.1f}%")
                m2.metric("Evolución de Tendencia", alerta_q2 if alerta_q2 else "Línea base inicial", delta_color="off")
                m3.metric("NPS Cortesía y Trato", f"{v_q4:.1f}%")
                m4.metric("NPS Info Pre-Entrega", f"{v_q8:.1f}%")
                
                st.markdown("---")
                st.subheader("📈 Evolución Histórica Mensual (NPS Recomendación)")
                if not df_evolucion.empty:
                    fig_linea = px.line(
                        df_evolucion, 
                        x="Periodo_Str", 
                        y="NPS", 
                        text=df_evolucion["NPS"].round(1).astype(str) + "%",
                        labels={"Periodo_Str": "Mes", "NPS": "NPS Principal %"},
                        markers=True
                    )
                    fig_linea.add_hline(y=94, line_dash="dash", line_color="green", annotation_text="Objetivo (94%)")
                    fig_linea.update_traces(textposition="top center", line=dict(color='#007bff', width=3))
                    fig_linea.update_layout(yaxis=dict(range=[-10, 110]), height=280, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_linea, use_container_width=True, key="linea_ind_autociel_v3")
                else:
                    st.info("Sin registros previos para armar evolutivos.")
                
                st.markdown("---")
                st.subheader(f"💬 Comentarios específicos del asesor {vendedor_sel}")
                df_v_individual = df_vend[["Fecha de ultimo contacto", "Nombre de cliente", MAPA['q3'], MAPA['q2']]].copy()
                df_v_individual = df_v_individual.sort_values("Fecha de ultimo contacto", ascending=False)
                df_v_individual["Fecha de ultimo contacto"] = df_v_individual["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_v_individual.rename(columns={MAPA['q3']: 'Feedback obtenido', MAPA['q2']: 'Calificación'}), 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.warning("No se encontraron asesores comerciales para estos filtros.")

except Exception as e:
    st.error(f"Error en la ejecución del Tablero Autociel: {e}")
