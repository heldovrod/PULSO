import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

from models.paciente import PacienteFHIR
from core.risk_engine import evaluar, clave_orden
from core.clinical_rules import OBJETIVO_LDL

# Configuración de la página
st.set_page_config(page_title="Dashboard Clínico | PULSO", page_icon=":material/analytics:", layout="wide")

st.title(":material/analytics: Análisis Clínico del Paciente")
st.caption("Visualización clínica interactiva")

# 1. CARGA DE DATOS
@st.cache_data
def cargar_pacientes_evaluados():
    ruta_datos = Path(__file__).parent.parent / "data" / "patients.json"
    hoy = datetime(2026, 11, 14)
    
    try:
        with open(ruta_datos, "r", encoding="utf-8") as f:
            pacientes_crudos = json.load(f)
    except FileNotFoundError:
        return None
        
    resultados = []
    for datos in pacientes_crudos:
        try:
            paciente_val = PacienteFHIR(**datos)
            resultado = evaluar(paciente_val.model_dump(), hoy)
            resultados.append({"paciente": paciente_val, "resultado": resultado})
        except Exception:
            pass
            
    resultados.sort(key=lambda x: clave_orden(x["resultado"]))
    return resultados

datos_evaluados = cargar_pacientes_evaluados()

if datos_evaluados is None:
    st.error("No se encontraron los datos.")
    st.stop()

# 2. SELECTOR DE PACIENTE
opciones_pacientes = {
    f"{item['paciente'].nombre} ({item['resultado']['categoria']})": item 
    for item in datos_evaluados
}

default_index = 0
if "paciente_seleccionado" in st.session_state:
    target_id = st.session_state.paciente_seleccionado
    for idx, (key, val) in enumerate(opciones_pacientes.items()):
        if val["paciente"].id == target_id:
            default_index = idx
            break

paciente_seleccionado_str = st.selectbox(
    "🔍 Selecciona un paciente para analizar su evolución:", 
    options=list(opciones_pacientes.keys()),
    index=default_index
)

item_seleccionado = opciones_pacientes[paciente_seleccionado_str]
p = item_seleccionado["paciente"]
r = item_seleccionado["resultado"]

st.markdown("---")

# 3. CABECERA (Estilo Ficha de Paciente)
col1, col2 = st.columns([2.5, 1.5])
with col1:
    st.subheader(f":material/person: {p.nombre}")
    st.caption(f"**{p.edad} años** | {p.sexo.capitalize()} | CIP: {p.id}")
with col2:
    st.metric(
        label="CATEGORÍA CLÍNICA", 
        value=r["categoria"], 
        delta="Riesgo Crítico" if r["categoria"] == "Muy alto" else "",
        delta_color="inverse"
    )

st.markdown("---")

# 4. GRÁFICOS
col_graf1, col_graf2 = st.columns(2)

# --- GRÁFICO 1: Evolución del eGFR ---
with col_graf1:
    st.markdown("##### :material/monitor_heart: Función Renal (eGFR)")
    if p.series and p.series.egfr:
        df_egfr = pd.DataFrame(p.series.egfr, columns=["Fecha", "eGFR"])
        df_egfr["Fecha"] = pd.to_datetime(df_egfr["Fecha"])
        df_egfr = df_egfr.sort_values("Fecha")
        df_egfr["Fecha_str"] = df_egfr["Fecha"].dt.strftime("%d %b %Y")

        fig_egfr = go.Figure()
        
        # Línea principal
        fig_egfr.add_trace(go.Scatter(
            x=df_egfr["Fecha_str"], y=df_egfr["eGFR"],
            mode="lines+markers+text",
            text=df_egfr["eGFR"].round(0),
            textposition="top center",
            line=dict(color="#005B8F", width=3),
            marker=dict(size=8, color="#005B8F"),
            name="eGFR"
        ))
        
        # Zona de riesgo ERC (Sutil)
        fig_egfr.add_hrect(y0=0, y1=60, line_width=0, fillcolor="rgba(211, 47, 47, 0.05)", layer="below")
        fig_egfr.add_hline(y=60, line_dash="dot", line_color="#D32F2F", line_width=1.5, annotation_text="Umbral ERC")
        
        # Ajustamos el eje Y
        min_egfr = df_egfr["eGFR"].min()
        max_egfr = df_egfr["eGFR"].max()
        fig_egfr.update_layout(
            margin=dict(l=10, r=10, t=30, b=10), height=300,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[max(0, min_egfr - 20), max(100, max_egfr + 20)], showgrid=False, title=""),
            xaxis=dict(showgrid=False, title=""),
            showlegend=False
        )
        st.plotly_chart(fig_egfr, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No hay datos de evolución renal.")

# --- GRÁFICO 2: Evolución de la Presión Arterial ---
with col_graf2:
    st.markdown("##### :material/blood_pressure: Evolución de la Presión Arterial")
    if p.pa_tomas:
        df_pa = pd.DataFrame(p.pa_tomas, columns=["Sistólica", "Diastólica"])
        df_pa["Visita"] = [f"Visita {i+1}" for i in range(len(df_pa))]

        fig_pa = go.Figure()
        
        # Zona de riesgo (Sistólica > 140) - Muy sutil
        fig_pa.add_hrect(y0=140, y1=200, line_width=0, fillcolor="rgba(211, 47, 47, 0.04)", layer="below")
        
        # Línea Sistólica
        fig_pa.add_trace(go.Scatter(
            x=df_pa["Visita"], y=df_pa["Sistólica"], mode="lines+markers+text",
            text=df_pa["Sistólica"], textposition="top right",
            line=dict(color="#D32F2F", width=3), marker=dict(size=8),
            name="Sistólica"
        ))
        
        # Línea Diastólica
        fig_pa.add_trace(go.Scatter(
            x=df_pa["Visita"], y=df_pa["Diastólica"], mode="lines+markers+text",
            text=df_pa["Diastólica"], textposition="bottom right",
            line=dict(color="#1976D2", width=3), marker=dict(size=8),
            name="Diastólica"
        ))

        # Línea objetivo 140
        fig_pa.add_hline(y=140, line_dash="dot", line_color="#D32F2F", line_width=1.5, annotation_text="Objetivo Sistólica")

        fig_pa.update_layout(
            margin=dict(l=10, r=10, t=30, b=10), height=300,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[50, 200], showgrid=False, zeroline=False, title="mmHg"),
            xaxis=dict(showgrid=False, title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
        )
        st.plotly_chart(fig_pa, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No hay datos de presión arterial.")

# 5. FILA 2: LDL (Gauge) y Alertas (Barras)
col3, col4 = st.columns(2)

# --- GRÁFICO 3: Gauge LDL ---
with col3:
    st.markdown("##### :material/water_drop: Colesterol LDL vs Objetivo")
    if p.ldl is not None:
        objetivo = OBJETIVO_LDL.get(r["categoria"], 100)
        color_barra = "#D32F2F" if p.ldl > objetivo else "#388E3C"
        
        # 💡 CORRECCIÓN: Ajustamos altura y márgenes para que no se corte
        fig_ldl = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = p.ldl,
            number = {'suffix': " mg/dL", 'font': {'size': 32, 'color': color_barra}},
            title = {'text': f"Objetivo: &lt;{objetivo} mg/dL", 'font': {'size': 14}},
            gauge = {
                'axis': {'range': [0, 200], 'tickwidth': 1, 'tickcolor': "gray"},
                'bar': {'color': color_barra, 'thickness': 0.25},
                'bgcolor': "white",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, objetivo], 'color': 'rgba(56, 142, 60, 0.1)'},
                    {'range': [objetivo, 200], 'color': 'rgba(211, 47, 47, 0.1)'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.75,
                    'value': objetivo
                }
            }
        ))
        # 💡 CORRECCIÓN: Altura fija y margen inferior para que respire
        fig_ldl.update_layout(margin=dict(l=30, r=30, t=50, b=20), height=280, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_ldl, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("No hay datos de LDL.")

# --- GRÁFICO 4: Alertas Visuales ---
with col4:
    st.markdown("##### :material/notification_important: Gravedad de las Alertas")
    if r["alertas"]:
        conteo = {"Grave": 0, "Moderado": 0, "Leve": 0}
        for a in r["alertas"]:
            if a["nivel"] in conteo:
                conteo[a["nivel"]] += 1
                
        categorias = list(conteo.keys())
        valores = list(conteo.values())
        colores = ["#D32F2F", "#F57C00", "#FBC02D"]
        
        fig_alertas = go.Figure(go.Bar(
            x=valores,
            y=categorias,
            orientation='h',
            marker_color=colores,
            text=valores,
            textposition='inside',
            textfont=dict(color='white', size=14)
        ))
        
        fig_alertas.update_layout(
            margin=dict(l=10, r=10, t=30, b=10), height=280,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=13)),
            showlegend=False
        )
        st.plotly_chart(fig_alertas, use_container_width=True, config={'displayModeBar': False})
    else:
        # 💡 CORRECCIÓN: Si no hay alertas, mostramos un bloque de éxito limpio
        with st.container(border=True):
            st.write("")
            st.write("")
            st.success("Sin alertas clínicas activas.", icon=":material/check_circle:")
            st.write("")
            st.write("")

# 6. BOTÓN DE ACCIÓN
st.markdown("---")
if st.button(f"Ver Ficha Completa de {p.nombre}", type="primary", use_container_width=True, icon=":material/description:"):
    st.session_state.paciente_seleccionado = p.id
    st.switch_page("views/5_FichaPaciente.py")