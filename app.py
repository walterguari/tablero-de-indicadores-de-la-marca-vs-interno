import streamlit st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

# Enlaces a las diferentes pestañas del mismo Google Sheets
URL_MARCA = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"
URL_INTERNA = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=1131519764"

# --- FUNCIONES DE DATOS Y CÁLCULOS ---
@st.cache_data(ttl=600)  # Optimización: guarda en caché los datos por 10 minutos
def load_data(url, tipo_base):
    try:
        csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=").replace("/edit?gid=", "/export?format=csv&gid=")
        df = pd.read_csv(csv_url)
        
        # Normalización según el origen de la base de datos
        if tipo_base == "Encuestas de Marca":
            df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
            col_q1 = 'Q1 - Satisfacción general'
            col_q2 = 'Q2 - Recomendación - Concesionario'
            
        else:  # Encuestas Internas
            df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de último contacto"], dayfirst=True, errors='coerce')
            df["MARCA"] = df["MARCA"]
            df["Canal de Venta"] = df["CANAL DE VENTA"]
            df["Vendedor"] = df["VENDEDOR"]
            col_q1 = '1. Basándose en su experiencia de compra, ¿Recomendaría el Concesionario a Familiares y amigos?'
            col_q2 = '1. Basándose en su experiencia de compra, ¿Recomendaría el Concesionario a Familiares y amigos?'
            
            # --- DETECTOR AUTOMÁTICO DE COLUMNA DE CLIENTE PARA LA BASE INTERNA ---
            # Buscamos variantes comunes para evitar el error "not in index"
            posibles_columnas = ["Nombre de cliente", "Cliente", "Nombre", "NOMBRE", "CLIENTE", "Nombre y Apellido", "Apellido y Nombre"]
            col_encontrada = False
            for col in posibles_columnas:
                if col in df.columns:
                    df["Nombre de cliente"] = df[col]
                    col_encontrada = True
                    break
            if not col_encontrada:
                # Si no encuentra ninguna, creamos la columna vacía con "Anónimo" para que el dataframe funcione igual
                df["Nombre de cliente"] = "Anónimo"
        
        def categorizar_nps(val):
            val = pd.to_numeric(val, errors='coerce')
            if val >= 9: return "Promotor"
            if val >= 7: return "Neutro"
            if val <= 6: return "Detractor"
            return "Sin Datos"
        
        if col_q1 in df.columns:
            df['Cat_Q1'] = df[col_q1].apply(categorizar_nps)
        else:
            df['Cat_Q1'] = "Sin Datos"
            
        if col_q2 in df.columns:
            df['Cat_Q2'] = df[col_q2].apply(categorizar_nps)
        else:
            df['Cat_Q2'] = "Sin Datos"
            
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
        title = {'text': f"<b>{titulo}</b>", 'font': {'size': 18, 'color': '#333'}},
        number = {'suffix': "%", 'font': {'size': 40}},
        gauge = {
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color_viva, 'thickness': 0.15},
            'bgcolor': "#f0f0f0",
            'threshold': {'line': {'color': "black", 'width': 3}, 'thickness': 0.8, 'value': 94}
        }
    ))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=40, b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def crear_grafico_torta(df, columna, titulo):
    if columna not in df.columns:
        return go.Figure()
    conteo = df[columna].value_counts().reset_index()
    conteo.columns = [columna, 'Cantidad']
    fig = px.pie(conteo, values='Cantidad', names=columna, title=titulo, hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label+value')
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
    return fig

# --- LÓGICA PRINCIPAL ---
try:
    # --- FILTRO ORIGEN DE DATOS ---
    st.sidebar.header("Fuente de Información")
    base_seleccionada = st.sidebar.radio(
        "Seleccione Origen de Encuestas",
        options=["Encuestas de Marca", "Encuestas Internas"]
    )
    
    sheet_url = URL_MARCA if base_seleccionada == "Encuestas de Marca" else URL_INTERNA
    df = load_data(sheet_url, base_seleccionada)
    
    if not df.empty:
        # --- DICCIONARIO DINÁMICO DE COLUMNAS (MAPEO) ---
        if base_seleccionada == "Encuestas de Marca":
            MAPA = {
                'q1': 'Q1 - Satisfacción general',
                'q2': 'Q2 - Recomendación - Concesionario',
                'q3': 'Q3 - Verbalización',
                'q4': 'Q4 - Cortesía y amabilidad',
                'q5': 'Q5 - Competencia Vendedor',
                'lbl_q1': 'Q1 - SATISFACCIÓN',
                'lbl_q2': 'Q2 - RECOMENDACIÓN'
            }
        else:
            MAPA = {
                'q1': '1. Basándose en su experiencia de compra, ¿Recomendaría el Concesionario a Familiares y amigos?',
                'q2': '1. Basándose en su experiencia de compra, ¿Recomendaría el Concesionario a Familiares y amigos?',
                'q3': '8. Según tu experiencia, ¿qué aspectos te gustaron más y qué nos recomendarías mejorar?',
                'q4': '2. ¿Cómo califica la cortesía y amabilidad del Vendedor / Asesor Comercial?',
                'q5': '2. ¿Cómo califica la cortesía y amabilidad del Vendedor / Asesor Comercial?', 
                'lbl_q1': 'RECOMENDACIÓN (INTERNA)',
                'lbl_q2': 'RECOMENDACIÓN (INTERNA)'
            }

        # --- SIDEBAR (FILTROS GLOBALES) ---
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

        # --- DATA BASE FINAL ---
        df_base = df_time[(df_time["MARCA"].isin(marcas)) & (df_time["Canal de Venta"].isin(canales))]

        st.title(f"📊 Gestión de Calidad - {base_seleccionada}")
        
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
            
            nps_q1, p_q1, n_q1, d_q1, t_q1 = calcular_nps_detallado(df_base[MAPA['q1']])
            nps_q2, p_q2, n_q2, d_q2, _ = calcular_nps_detallado(df_base[MAPA['q2']])

            c_q1, c_q2, c_tot = st.columns([2.2, 2.2, 0.6])
            with c_q1:
                st.plotly_chart(crear_gauge_moderno(nps_q1, MAPA['lbl_q1']), use_container_width=True, key="gauge_global_q1")
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
                st.plotly_chart(crear_gauge_moderno(nps_q2, MAPA['lbl_q2']), use_container_width=True, key="gauge_global_q2")
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
                if st.button("🔄 Ver\nTodos", key="btn_ver_todos_global"): 
                    st.session_state.filtro_val = "Todos"
                    st.rerun()

            st.markdown("---")
            
            if base_seleccionada == "Encuestas de Marca":
                stabs = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
                with stabs[0]:
                    v1, v2, v3 = st.columns(3)
                    v1.metric("Q4 - Cortesía", f"{calcular_nps_detallado(df_base['Q4 - Cortesía y amabilidad'])[0]:.1f}%")
                    v2.metric("Q5 - Competencia", f"{calcular_nps_detallado(df_base['Q5 - Competencia Vendedor'])[0]:.1f}%")
                    v3.metric("Q8 - Info Pre-entrega", f"{calcular_nps_detallado(df_base['Q8 - Satisfacción información entre compra y entrega'])[0]:.1f}%")
                with stabs[1]:
                    ct1, ct2 = st.columns(2)
                    ct1.metric("Q7 - NPS Test Drive", f"{calcular_nps_detallado(df_base['Q7 - Satisfacción Test Drive'])[0]:.1f}%")
                    st.plotly_chart(crear_grafico_torta(df_base, 'Q6 - Ofrecimiento Test Drive', 'Q6 - Ofrecimiento TD'), use_container_width=True, key="torta_td_marca")
                with stabs[2]:
                    cf1, cf2 = st.columns(2)
                    cf1.metric("Q10 - NPS Financiación", f"{calcular_nps_detallado(df_base['Q10 - Satisfacción Financiación utilizada'])[0]:.1f}%")
                    st.plotly_chart(crear_grafico_torta(df_base, 'Q9 - Financiación utilizada', 'Mix Financiación'), use_container_width=True, key="torta_fin_marca")
                with stabs[3]:
                    ce1, ce2 = st.columns(2)
                    ce1.metric("Q11 - Momento Entrega", f"{calcular_nps_detallado(df_base['Q11 - Satisfacción Momento de la entrega'])[0]:.1f}%")
                    ce2.metric("Q13 - Entrega General", f"{calcular_nps_detallado(df_base['Q13 - Satisfacción Entrega General'])[0]:.1f}%")
            
            else:  
                stabs_int = st.tabs(["🤝 Trato Comercial", "📦 Procesos y Entrega", "📞 Seguimiento Postventa"])
                with stabs_int[0]:
                    v1, v2 = st.columns(2)
                    v1.metric("Cortesía y Amabilidad (Preg. 2)", f"{calcular_nps_detallado(df_base['2. ¿Cómo califica la cortesía y amabilidad del Vendedor / Asesor Comercial?'])[0]:.1f}%")
                    st.plotly_chart(crear_grafico_torta(df_base, '3. ¿Le han ofrecido una prueba de manejo?', 'Mix Ofrecimiento Test Drive'), use_container_width=True, key="torta_td_interna")
                with stabs_int[1]:
                    e1, e2 = st.columns(2)
                    e1.metric("Info Pre-entrega (Preg. 4)", f"{calcular_nps_detallado(df_base['4. ¿Cómo califica la información facilitada entre la compra y la entrega de su vehículo nuevo? (Comunicación y explicación de tramites administrativos)'])[0]:.1f}%")
                    e2.metric("Presentación 0KM (Preg. 5)", f"{calcular_nps_detallado(df_base['5. ¿Cómo califica la presentación de su 0KM al momento de la entrega? (explicaciones de las características, la limpieza y la presentación con el vehículo, entre otros aspectos.)'])[0]:.1f}%")
                with stabs_int[2]:
                    p1, p2 = st.columns(2)
                    st.plotly_chart(crear_grafico_torta(df_base, '6. ¿Recibió un contacto del concesionario posterior a la entrega de su vehículo? (vía whatsapp, sms, correo o llamado)', 'Contacto Postventa Realizado'), use_container_width=True, key="torta_post_interna")
                    p2.metric("Satisfacción Contacto (Preg. 7)", f"{calcular_nps_detallado(df_base['7. ¿Cuán satisfecho se encuentra con el contacto posterior realizado por el concesionario?'])[0]:.1f}%")

            st.markdown("---")
            label_f = "Todos los comentarios" if st.session_state.filtro_val == "Todos" else f"Comentarios: {st.session_state.filtro_val} ({st.session_state.filtro_col.replace('Cat_', '')})"
            st.subheader(f"💬 Verbalizaciones - {label_f}")
            df_v = df_base[["Fecha de ultimo contacto", "Nombre de cliente", MAPA['q3'], "Vendedor", "Cat_Q1", "Cat_Q2"]].copy()
            if st.session_state.filtro_val != "Todos":
                df_v = df_v[df_v[st.session_state.filtro_col] == st.session_state.filtro_val]
            
            df_v = df_v.sort_values("Fecha de ultimo contacto", ascending=False)
            df_v["Fecha de ultimo contacto"] = df_v["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
            st.dataframe(df_v[["Fecha de ultimo contacto", "Nombre de cliente", MAPA['q3'], "Vendedor"]].rename(columns={MAPA['q3']: 'Comentarios / Oportunidades'}), use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 2: TABLA MASTER UNIFICADA (CON SEMÁFOROS)
        # ==========================================================
        with tab_unificada:
            st.header("Ranking Ejecutivo Unificado de Asesores")
            
            if not df_base.empty:
                resumen_master = []
                for vend, data in df_base.groupby("Vendedor"):
                    n_q2, p_q2, _, d_q2, t_q2 = calcular_nps_detallado(data[MAPA['q2']])
                    n_q4, _, _, _, _ = calcular_nps_detallado(data[MAPA['q4']])
                    n_q5, _, _, _, _ = calcular_nps_detallado(data[MAPA['q5']])
                    
                    resumen_master.append({
                        "Vendedor": vend,
                        "NPS Principal / Recomendación": round(n_q2, 1),
                        "Faltante Obj. 94%": calcular_faltante_94(p_q2, d_q2, t_q2),
                        "NPS Cortesía / Amabilidad": round(n_q4, 1),
                        "NPS Competencia / Secundario": round(n_q5, 1),
                        "Encuestas Muestra": t_q2
                    })
                
                df_master = pd.DataFrame(resumen_master).sort_values("NPS Principal / Recomendación", ascending=False)
                
                def color_celda_nps(val):
                    try:
                        v = float(val)
                        if v >= 94: return 'background-color: #d4edda; color: #155724; font-weight: bold'
                        if v >= 90: return 'background-color: #fff3cd; color: #856404; font-weight: bold'
                        return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                    except:
                        return ''

                df_styled = df_master.style.map(color_celda_nps, subset=["NPS Principal / Recomendación", "NPS Cortesía / Amabilidad", "NPS Competencia / Secundario"])\
                                           .map(lambda x: 'color: #721c24; font-weight: bold' if '🚨' in str(x) else 'color: #155724', subset=['Faltante Obj. 94%'])
                
                st.dataframe(df_styled, use_container_width=True, hide_index=True)

        # ==========================================================
        # TAB 3: FICHA INDIVIDUAL POR ASESOR (EVOLUCIÓN TEMPORAL)
        # ==========================================================
        with tab_individual:
            st.header("Análisis de Evolución por Asesor Comercial")
            
            vendedores_disponibles = sorted(df_base["Vendedor"].dropna().unique())
            if vendedores_disponibles:
                vendedor_sel = st.selectbox("Seleccione el Asesor a Evaluar", options=vendedores_disponibles, key="select_vendedor_individual")
                df_vend = df_base[df_base["Vendedor"] == vendedor_sel]
                
                # --- CÁLCULO DE ALERTAS MES CONTRA MES (TENDENCIA) ---
                df_vend_full = df[(df["Vendedor"] == vendedor_sel) & (df["MARCA"].isin(marcas)) & (df["Canal de Venta"].isin(canales))].copy()
                df_vend_full["Periodo"] = df_vend_full["Fecha de ultimo contacto"].dt.to_period("M")
                
                resumen_mensual = []
                for per, data_m in df_vend_full.groupby("Periodo"):
                    n_m, _, _, _, _ = calcular_nps_detallado(data_m[MAPA['q2']])
                    resumen_mensual.append({"Periodo_Str": str(per), "Periodo": per, "NPS": n_m})
                
                df_evolucion = pd.DataFrame(resumen_mensual).sort_values("Periodo")
                
                st.markdown(f"### Historial de Rendimiento: **{vendedor_sel}**")
                
                v_q2, pv2, _, dv2, tv2 = calcular_nps_detallado(df_vend[MAPA['q2']])
                v_q4, _, _, _, _ = calcular_nps_detallado(df_vend[MAPA['q4']])
                v_q5, _, _, _, _ = calcular_nps_detallado(df_vend[MAPA['q5']])
                
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
                m1.metric("NPS Indicador Principal", f"{v_q2:.1f}%")
                m2.metric("Tendencia vs Mes Anterior", alerta_q2 if alerta_q2 else "Muestra inicial", delta_color="off")
                m3.metric("NPS Cortesía / Trato", f"{v_q4:.1f}%")
                m4.metric("NPS Competencia / Proceso", f"{v_q5:.1f}%")
                
                # --- GRÁFICO DE LÍNEAS TEMPORAL ---
                st.markdown("---")
                st.subheader("📈 Línea de Tiempo - Evolución de NPS")
                if not df_evolucion.empty:
                    fig_linea = px.line(
                        df_evolucion, 
                        x="Periodo_Str", 
                        y="NPS", 
                        text=df_evolucion["NPS"].round(1).astype(str) + "%",
                        labels={"Periodo_Str": "Mes de Auditoría", "NPS": "NPS Principal %"},
                        markers=True
                    )
                    fig_linea.add_hline(y=94, line_dash="dash", line_color="green", annotation_text="Objetivo 94%")
                    fig_linea.update_traces(textposition="top center", line=dict(color='#007bff', width=3))
                    fig_linea.update_layout(yaxis=dict(range=[-10, 110]), height=300, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_linea, use_container_width=True, key="grafico_evolucion_vendedor_master_final_v2")
                else:
                    st.info("Sin historial suficiente para trazar línea de tiempo.")
                
                # --- EXCLUSIVO VERBALIZACIONES DEL ASESOR ---
                st.markdown("---")
                st.subheader(f"💬 Comentarios de Clientes asignados a {vendedor_sel}")
                df_v_individual = df_vend[["Fecha de ultimo contacto", "Nombre de cliente", MAPA['q3'], MAPA['q2']]].copy()
                df_v_individual = df_v_individual.sort_values("Fecha de ultimo contacto", ascending=False)
                df_v_individual["Fecha de ultimo contacto"] = df_v_individual["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
                
                st.dataframe(
                    df_v_individual.rename(columns={MAPA['q3']: 'Feedback del Cliente', MAPA['q2']: 'Nota Principal'}), 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.warning("No se encontraron asesores con los filtros seleccionados.")

except Exception as e:
    st.error(f"Error crítico en la ejecución del tablero multicanal: {e}")
