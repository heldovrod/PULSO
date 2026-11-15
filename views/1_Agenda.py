import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timedelta

from models.paciente import PacienteFHIR
from core.risk_engine import evaluar

# Configuración de la página
st.set_page_config(page_title="Agenda Diaria | PULSO", page_icon=":material/calendar_month:", layout="wide")

st.title(":material/calendar_month: Agenda Diaria de Consulta")
st.caption("Pacientes citados para hoy y sus alertas clínicas previas a la visita.")

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
            
    return resultados

datos_evaluados = cargar_pacientes_evaluados()

if datos_evaluados is None:
    st.error("No se encontraron los datos. Ejecuta 'python scripts/generate_dataset.py' primero.")
    st.stop()

# 💡 NUEVO: BUSCADOR EN LA PANTALLA PRINCIPAL
st.markdown("---")
busqueda = st.text_input("🔍 Buscador rápido: Introduce nombre o CIP para buscar en todo el cupo...", "")

if busqueda:
    resultados_busqueda = [
        item for item in datos_evaluados 
        if busqueda.lower() in item["paciente"].nombre.lower() or busqueda.lower() in item["paciente"].id.lower()
    ]
    
    if not resultados_busqueda:
        st.warning(f"No se han encontrado pacientes que coincidan con '{busqueda}'.")
    else:
        st.write(f"### Resultados de la búsqueda ({len(resultados_busqueda)})")
        
        for item in resultados_busqueda[:15]: # Límite visual de 15
            p = item["paciente"]
            r = item["resultado"]
            alertas_ord = sorted(r["alertas"], key=lambda x: {"Grave":3, "Moderado":2, "Leve":1}.get(x["nivel"], 0), reverse=True)
            
            with st.container(border=True):
                c_info, c_alertas, c_botones = st.columns([3, 5, 1.2], vertical_alignment="center")
                
                with c_info:
                    st.markdown(f"**{p.nombre}**")
                    st.caption(f"{p.edad} años | {p.id}")
                    
                    if r["categoria"] == "Muy alto":
                        st.markdown(":red-background[**Riesgo Muy alto**]")
                    elif r["categoria"] == "Alto":
                        st.markdown(":orange-background[**Riesgo Alto**]")
                    elif r["categoria"] == "Moderado":
                        st.markdown(":yellow-background[**Riesgo Moderado**]")
                    
                with c_alertas:
                    if not alertas_ord:
                        st.success("Sin alertas relevantes", icon=":material/check_circle:")
                    else:
                        alerta_top = alertas_ord[0]
                        if alerta_top["nivel"] == "Grave":
                            st.error(f"**{alerta_top['tipo']}:** {alerta_top['texto']}", icon=":material/error:")
                        elif alerta_top["nivel"] == "Moderado":
                            st.warning(f"**{alerta_top['tipo']}:** {alerta_top['texto']}", icon=":material/warning:")
                        else:
                            st.info(f"**{alerta_top['tipo']}:** {alerta_top['texto']}", icon=":material/info:")
                            
                with c_botones:
                    if st.button("Abrir Ficha", key=f"search_btn_{p.id}", type="primary", use_container_width=True):
                        st.session_state.paciente_seleccionado = p.id
                        st.switch_page("views/5_FichaPaciente.py")
    
    # Si estamos buscando, ocultamos la agenda normal para que no haya conflicto visual
    st.stop()

# 2. SIMULACIÓN DE LA AGENDA (Si no hay búsqueda activa)
pacientes_citados = datos_evaluados[:12]

hora_inicio = datetime(2026, 11, 14, 8, 30)
citas_hoy = []
for i, item in enumerate(pacientes_citados):
    hora_cita = hora_inicio + timedelta(minutes=20 * i) 
    citas_hoy.append({"hora": hora_cita.strftime("%H:%M"), "item": item})

citas_hoy.sort(key=lambda x: x["hora"])

# 3. INTERFAZ VISUAL DE LA AGENDA
col_agenda, col_resumen = st.columns([4.5, 1.2])

with col_agenda:
    st.markdown("### :material/schedule: Horario de Consulta")
    
    for cita in citas_hoy:
        hora = cita["hora"]
        p = cita["item"]["paciente"]
        r = cita["item"]["resultado"]
        
        alertas_ord = sorted(r["alertas"], key=lambda x: {"Grave":3, "Moderado":2, "Leve":1}.get(x["nivel"], 0), reverse=True)
        
        with st.container(border=True):
            c_hora, c_info, c_alertas, c_botones = st.columns([1, 2.8, 5, 1.2], vertical_alignment="center")
            
            # Hora en azul institucional nativo
            with c_hora:
                st.markdown(f"### :blue[**{hora}**]")
                
            with c_info:
                st.markdown(f"**{p.nombre}**")
                st.caption(f"{p.edad} años | {p.id}")
                
                # Badges nativos de Streamlit
                if r["categoria"] == "Muy alto":
                    st.markdown(":red-background[**Riesgo Muy alto**]")
                elif r["categoria"] == "Alto":
                    st.markdown(":orange-background[**Riesgo Alto**]")
                elif r["categoria"] == "Moderado":
                    st.markdown(":yellow-background[**Riesgo Moderado**]")
                # Si es "Bajo", no ponemos nada.
                
            with c_alertas:
                if not alertas_ord:
                    st.success("Sin alertas relevantes", icon=":material/check_circle:")
                else:
                    alerta_top = alertas_ord[0]
                    
                    if alerta_top["nivel"] == "Grave":
                        st.error(f"**{alerta_top['tipo']}:** {alerta_top['texto']}", icon=":material/error:")
                    elif alerta_top["nivel"] == "Moderado":
                        st.warning(f"**{alerta_top['tipo']}:** {alerta_top['texto']}", icon=":material/warning:")
                    else:
                        st.info(f"**{alerta_top['tipo']}:** {alerta_top['texto']}", icon=":material/info:")
                        
                    if len(alertas_ord) > 1:
                        st.caption(f"*+ {len(alertas_ord) - 1} alertas más en la ficha*")
                                    
            with c_botones:
                if st.button("Abrir", key=f"btn_{p.id}", type="secondary", use_container_width=True, icon=":material/arrow_forward:"):
                    st.session_state.paciente_seleccionado = p.id
                    st.switch_page("views/5_FichaPaciente.py")

with col_resumen:
    # Título nativo con icono (se alinea solo con el de la izquierda)
    st.markdown("### :material/analytics: Resumen")
    
    with st.container(border=True):
        total_citas = len(citas_hoy)
        citas_criticas = sum(1 for c in citas_hoy if c["item"]["resultado"]["categoria"] == "Muy alto")
        citas_con_alertas = sum(1 for c in citas_hoy if len(c["item"]["resultado"]["alertas"]) > 0)
        
        # Métricas directas sin columnas fantasma
        st.metric("Citas", total_citas)
        st.metric("Críticos", citas_criticas)
        st.metric("Alertas", citas_con_alertas)
        
        st.divider()
        st.caption(":material/lightbulb: Revisa las alertas antes de la visita.")
