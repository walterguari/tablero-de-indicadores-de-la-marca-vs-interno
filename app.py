import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tablero de Indicadores - Cenoa", layout="wide")

sheet_url = "https://docs.google.com/spreadsheets/d/1p2xd-SNGEDZ_sT8P4xAjdLQEZ5uuEx57c3NhGOaBNTo/edit#gid=567460007"

def load_data(url):
    csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
    df = pd.read_csv(csv_url)
    df["Fecha de ultimo contacto"] = pd.to_datetime(df["Fecha de ultimo contacto"], dayfirst=True, errors='coerce')
    return df

def calcular_nps(serie):
    serie = pd.to_numeric(serie, errors='coerce').dropna()
    if serie.empty: return 0
    promotores = (serie >= 9).sum()
    detractores = (serie <= 6).sum()
    total = len(serie)
    return ((promotores - detractores) / total) * 100

def crear_grafico_torta(df, columna, titulo):
    conteo = df[columna].value_counts().reset_index()
    conteo.columns = [columna, 'Cantidad']
    fig = px.pie(conteo, values='Cantidad', names=columna, title=titulo, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_traces(textinfo='percent+label+value')
    return fig

try:
    df = load_data(sheet_url)
    
    # --- BARRA LATERAL (FILTROS DE PERÍODO Y MARCA) ---
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

    marca = st.sidebar.multiselect("MARCA", options=df["MARCA"].unique(), default=df["MARCA"].unique())
    canal = st.sidebar.multiselect("Canal de Venta", options=df["Canal de Venta"].unique(), default=df["Canal de Venta"].unique())

    # Data filtrada base (Sin filtro de vendedor)
    df_base = df[
        (df["Anio"] == anio_sel) & 
        (df["Mes_Num"] == mes_sel_num) &
        (df["MARCA"].isin(marca)) & 
        (df["Canal de Venta"].isin(canal))
    ]

    # --- NAVEGACIÓN PRINCIPAL ---
    st.title("📊 Sistema de Gestión de Calidad")
    pestana_principal, pestana_vendedores = st.tabs(["🏠 Monitor de Calidad Total", "👤 Rendimiento por Vendedor"])

    # --- PESTAÑA 1: MONITOR GLOBAL ---
    with pestana_principal:
        st.header(f"Resultados Globales - {mes_sel_nombre} {anio_sel}")
        k1, k2, k3 = st.columns(3)
        k1.metric("Q1 - NPS Satisfacción Gral.", f"{calcular_nps(df_base['Q1 - Satisfacción general']):.1f}%")
        k2.metric("Q2 - NPS Recomendación", f"{calcular_nps(df_base['Q2 - Recomendación - Concesionario']):.1f}%")
        k3.metric("Muestra Total", len(df_base))

        st.markdown("---")
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["🤝 Ventas", "🚗 Test Drive", "💰 Finanzas", "📦 Entrega"])
        
        with sub_tab1:
            c1, c2, c3 = st.columns(3)
            c1.metric("Q4 - Cortesía", f"{calcular_nps(df_base['Q4 - Cortesía y amabilidad']):.1f}%")
            c2.metric("Q5 - Competencia", f"{calcular_nps(df_base['Q5 - Competencia Vendedor']):.1f}%")
            c3.metric("Q8 - Info Pre-entrega", f"{calcular_nps(df_base['Q8 - Satisfacción información entre compra y entrega']):.1f}%")
        with sub_tab2:
            ct1, ct2 = st.columns(2)
            with ct1: st.plotly_chart(crear_grafico_torta(df_base, "Q6 - Ofrecimiento Test Drive", "Q6 - Ofrecimiento TD"), use_container_width=True)
            with ct2: st.metric("Q7 - NPS Test Drive", f"{calcular_nps(df_base['Q7 - Satisfacción Test Drive']):.1f}%")
        with sub_tab3:
            cf1, cf2 = st.columns(2)
            with cf1: st.plotly_chart(crear_grafico_torta(df_base, "Q9 - Financiación utilizada", "Q9 - Tipo de Pago"), use_container_width=True)
            with cf2: st.metric("Q10 - NPS Financiación", f"{calcular_nps(df_base['Q10 - Satisfacción Financiación utilizada']):.1f}%")
        with sub_tab4:
            ce1, ce2 = st.columns(2)
            ce1.metric("Q11 - Momento Entrega", f"{calcular_nps(df_base['Q11 - Satisfacción Momento de la entrega']):.1f}%")
            ce2.metric("Q13 - Entrega General", f"{calcular_nps(df_base['Q13 - Satisfacción Entrega General']):.1f}%")

    # --- PESTAÑA 2: RENDIMIENTO POR VENDEDOR ---
    with pestana_vendedores:
        st.header("Análisis Comparativo de Asesores")
        
        # Cálculo de NPS Q1 por Vendedor
        vendedor_nps = df_base.groupby("Vendedor").apply(lambda x: calcular_nps(x["Q1 - Satisfacción general"])).reset_index()
        vendedor_nps.columns = ["Vendedor", "NPS Q1 %"]
        
        # Conteo de encuestas por Vendedor
        vendedor_count = df_base["Vendedor"].value_counts().reset_index()
        vendedor_count.columns = ["Vendedor", "Cantidad Encuestas"]
        
        # Unimos los datos
        comparativa = pd.merge(vendedor_nps, vendedor_count, on="Vendedor")

        # Gráfico de barras comparativo
        fig_comp = px.bar(
            comparativa.sort_values("NPS Q1 %", ascending=False),
            x="Vendedor", y="NPS Q1 %",
            text="NPS Q1 %",
            color="NPS Q1 %",
            title="Ranking de NPS por Vendedor",
            color_continuous_scale="RdYlGn", # Rojo a Verde
            labels={"NPS Q1 %": "NPS (%)"}
        )
        fig_comp.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_comp, use_container_width=True)

        st.subheader("Tabla Detallada de Rendimiento")
        st.dataframe(comparativa.sort_values("NPS Q1 %", ascending=False), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("💬 Verbalizaciones Recientes")
        df_display = df_base[["Fecha de ultimo contacto", "Nombre de cliente", "Vendedor", "Q3 - Verbalización"]].copy()
        df_display["Fecha de ultimo contacto"] = df_display["Fecha de ultimo contacto"].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display.sort_values("Vendedor"), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
