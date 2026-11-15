import streamlit as st
import json
from pathlib import Path
from datetime import datetime

from models.paciente import PacienteFHIR
from core.risk_engine import evaluar, clave_orden
from core.clinical_rules import NIVELES

st.set_page_config(page_title="Pacientes Prioritarios | PULSO", page_icon=":material/groups:", layout="wide")

st.title(":material/groups: Directorio de Pacientes Prioritarios")
st.caption("Ranking clínico y filtros para la gestión del cupo")

RUTA_PACIENTES = Path(__file__).parent.parent / "data" / "patients.json"
RUTA_SEGUIMIENTO = Path(__file__).parent.parent / "data" / "seguimiento.json"

@st.cache_data
def cargar_datos_evaluados():
    hoy = datetime(2026, 11, 14)
    try:
        with open(RUTA_PACIENTES, "r", encoding="utf-8") as f:
            pacientes_crudos = json.load(f)
    except FileNotFoundError:
        return None
        
    resultados = []
    for datos in pacientes_crudos:
        try:
            paciente_val = PacienteFHIR(**datos)
            resultado = evaluar(paciente_val.model_dump(), hoy)
            resultado["alertas"].sort(key=lambda x: NIVELES.index(x["nivel"]), reverse=True)
            resultados.append({"paciente": paciente_val, "resultado": resultado})
        except Exception:
            pass
    resultados.sort(key=lambda x: clave_orden(x["resultado"]))
    return resultados

datos_evaluados = cargar_datos_evaluados()

if datos_evaluados is None:
    st.error("No se encontraron los datos.")
    st.stop()

# 💡 NUEVO: Leemos los estados del archivo JSON en cada recarga (no está cacheado, así que siempre está fresco)
if RUTA_SEGUIMIENTO.exists():
    with open(RUTA_SEGUIMIENTO, "r", encoding="utf-8") as f:
        db_seg = json.load(f)
    estados_seg = db_seg.get("estados", {})
else:
    estados_seg = {}

# --- FILTROS LATERALES ---
st.sidebar.markdown("### :material/filter_list: Filtros")
busqueda = st.sidebar.text_input("Buscar por Nombre o CIP:")
categorias = ["Muy alto", "Alto", "Moderado", "Bajo"]
cats_seleccionadas = st.sidebar.multiselect("Categoría de Riesgo:", categorias, default=["Muy alto", "Alto"])
rango_edad = st.sidebar.slider("Rango de Edad:", 0, 100, (0, 100))
mostrar_revisados = st.sidebar.checkbox("Mostrar pacientes ya revisados", value=False)

# --- APLICAR FILTROS ---
resultados_filtrados = []
for item in datos_evaluados:
    p = item["paciente"]
    r = item["resultado"]
    
    if r["categoria"] not in cats_seleccionadas: continue
    if not (rango_edad[0] <= p.edad <= rango_edad[1]): continue
    if busqueda and (busqueda.lower() not in p.nombre.lower() and busqueda.lower() not in p.id.lower()): continue
    
    estado_actual = estados_seg.get(p.id, "Pendiente")
    if not mostrar_revisados and estado_actual == "Revisado":
        continue
            
    resultados_filtrados.append(item)

# --- KPIs ---
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pacientes Filtrados", len(resultados_filtrados))
col2.metric(":red[Riesgo Muy Alto]", sum(1 for x in resultados_filtrados if x["resultado"]["categoria"] == "Muy alto"))
col3.metric(":orange[Riesgo Alto]", sum(1 for x in resultados_filtrados if x["resultado"]["categoria"] == "Alto"))
col4.metric(":material/error: Alertas Graves", sum(1 for x in resultados_filtrados if any(a["nivel"] == "Grave" for a in x["resultado"]["alertas"])))
st.markdown("---")

# --- LISTADO MINIMALISTA ---
st.write("### :material/list: Listado Priorizado")

if not resultados_filtrados:
    st.info("No hay pacientes que coincidan con los filtros seleccionados.")
else:
    h1, h2, h3, h4 = st.columns([3, 2.5, 4.5, 1.2])
    h1.markdown("<span style='color:#6B7280; font-size:0.8rem; font-weight:600;'>PACIENTE</span>", unsafe_allow_html=True)
    h2.markdown("<span style='color:#6B7280; font-size:0.8rem; font-weight:600;'>RIESGO</span>", unsafe_allow_html=True)
    h3.markdown("<span style='color:#6B7280; font-size:0.8rem; font-weight:600;'>ALERTA PRINCIPAL</span>", unsafe_allow_html=True)
    
    for item in resultados_filtrados:
        p = item["paciente"]
        r = item["resultado"]
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2.5, 4.5, 1.2], vertical_alignment="center")
            
            with c1:
                if st.button(p.nombre, key=f"link_{p.id}", type="tertiary"):
                    st.session_state.paciente_seleccionado = p.id
                    st.switch_page("views/5_FichaPaciente.py")
                st.caption(f"{p.edad} años | {p.id}")
                
            with c2:
                if r["categoria"] == "Muy alto":
                    st.markdown("<span style='background-color: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>🔴 Muy alto</span>", unsafe_allow_html=True)
                elif r["categoria"] == "Alto":
                    st.markdown("<span style='background-color: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>🟠 Alto</span>", unsafe_allow_html=True)
                elif r["categoria"] == "Moderado":
                    st.markdown("<span style='background-color: #FEF9C3; color: #854D0E; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>🟡 Moderado</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='background-color: #D1FAE5; color: #065F46; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>🟢 Bajo</span>", unsafe_allow_html=True)
                    
            with c3:
                if r["alertas"]:
                    st.markdown(f"<span style='color: #374151; font-size: 0.9rem;'>{r['alertas'][0]['texto']}</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: #9CA3AF; font-size: 0.9rem;'>Sin alertas</span>", unsafe_allow_html=True)
                    
            with c4:
                if st.button("Abrir", key=f"btn_{p.id}", type="secondary", use_container_width=True, icon=":material/arrow_forward:"):
                    st.session_state.paciente_seleccionado = p.id
                    st.switch_page("views/5_FichaPaciente.py")