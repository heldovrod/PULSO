import streamlit as st
import json
from pathlib import Path
from datetime import datetime

from models.paciente import PacienteFHIR
from core.risk_engine import evaluar, clave_orden
from core.clinical_rules import NIVELES

st.set_page_config(page_title="Oportunidades | PULSO", page_icon=":material/lightbulb:", layout="wide")

st.title(":material/lightbulb: Oportunidades Preventivas")
st.caption("Tareas pendientes agrupadas por tipo de intervención clínica")

# 1. CARGAR DATOS
ruta_datos = Path(__file__).parent.parent / "data" / "patients.json"
ruta_seguimiento = Path(__file__).parent.parent / "data" / "seguimiento.json"
hoy = datetime(2026, 11, 14)

try:
    # Cargamos los pacientes
    with open(ruta_datos, "r", encoding="utf-8") as f:
        pacientes_crudos = json.load(f)
        
    # Cargamos el estado del seguimiento
    if ruta_seguimiento.exists():
        with open(ruta_seguimiento, "r", encoding="utf-8") as f:
            db_seg = json.load(f)
        estados_seg = db_seg.get("estados", {})
    else:
        estados_seg = {}

    pacientes_evaluados = []
    
    for datos in pacientes_crudos:
        try:
            # Filtramos si ya está en seguimiento o revisado
            paciente_id = datos["id"]
            estado_actual = estados_seg.get(paciente_id, "Pendiente")
            
            if estado_actual in ["En seguimiento", "Revisado"]:
                continue # Si ya se está trabajando en él, lo saltamos

            paciente_val = PacienteFHIR(**datos)
            resultado = evaluar(paciente_val.model_dump(), hoy)
            resultado["alertas"].sort(key=lambda x: NIVELES.index(x["nivel"]), reverse=True)
            pacientes_evaluados.append({"paciente": paciente_val, "resultado": resultado})
        except Exception:
            pass

    pacientes_evaluados.sort(key=lambda x: clave_orden(x["resultado"]))

    # 2. CLASIFICACIÓN POR TIPO DE TAREA
    tareas_seguridad = []
    tareas_inercia = []
    tareas_cribado = []
    
    for item in pacientes_evaluados:
        r = item["resultado"]
        
        if any("CONTRAINDICACIÓN" in a["texto"] or "TRIPLE WHAMMY" in a["texto"] for a in r["alertas"]):
            tareas_seguridad.append(item)
        elif any("Inercia" in a["texto"] or "ajuste" in a["texto"].lower() for a in r["alertas"]):
            tareas_inercia.append(item)
        elif any("Albuminuria no registrada" in a["texto"] for a in r["alertas"]):
            tareas_cribado.append(item)

    # 3. RESUMEN VISUAL
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric(":red[Errores de Medicación]", len(tareas_seguridad), help="Pacientes con combinaciones de fármacos peligrosas")
    col2.metric(":orange[Inercia Terapéutica]", len(tareas_inercia), help="Pacientes descontrolados sin cambios de tratamiento")
    col3.metric(":blue[Cribados Pendientes]", len(tareas_cribado), help="Pacientes sin analítica de RAC reciente")
    st.markdown("---")

    # 4. FUNCIÓN PARA PINTAR UNA FILA COMPACTA
    def render_tarea_compacta(item):
        p = item["paciente"]
        r = item["resultado"]
        
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 5.5, 1.2], vertical_alignment="center")
            with c1:
                # Nombre clicable
                if st.button(p.nombre, key=f"link_task_{p.id}", type="tertiary"):
                    st.session_state.paciente_seleccionado = p.id
                    st.switch_page("views/5_FichaPaciente.py")
                st.caption(f"{p.edad} años | {p.id}")
            with c2:
                if r["alertas"]:
                    alerta = r["alertas"][0]
                    st.markdown(f"<span style='color: #374151; font-size: 0.9rem;'>{alerta['texto']}</span>", unsafe_allow_html=True)
            with c3:
                if st.button("Abrir", key=f"btn_task_{p.id}", type="secondary", use_container_width=True, icon=":material/arrow_forward:"):
                    st.session_state.paciente_seleccionado = p.id
                    st.switch_page("views/5_FichaPaciente.py")

    # 5. BLOQUES DESPLEGABLES
    with st.expander(f"🚨 Alertas de Seguridad Farmacológica ({len(tareas_seguridad)} pacientes)", expanded=True):
        st.write("Pacientes con combinaciones de fármacos contraindicadas o riesgo de toxicidad grave.")
        if not tareas_seguridad:
            st.success("No hay errores de medicación detectados en el cupo.")
        else:
            for item in tareas_seguridad[:5]:
                render_tarea_compacta(item)
            if len(tareas_seguridad) > 5:
                st.info(f"Mostrando los 5 más urgentes. Quedan {len(tareas_seguridad) - 5} más en la lista general.")

    with st.expander(f"💊 Inercia Terapéutica / Ajustes de Tratamiento ({len(tareas_inercia)} pacientes)"):
        st.write("Pacientes con parámetros descontrolados (PA, LDL, HbA1c) que no han tenido cambios en su medicación.")
        if not tareas_inercia:
            st.success("No hay casos de inercia terapéutica pendientes.")
        else:
            for item in tareas_inercia[:5]:
                render_tarea_compacta(item)
            if len(tareas_inercia) > 5:
                st.info(f"Mostrando los 5 más urgentes. Quedan {len(tareas_inercia) - 5} más en la lista.")

    with st.expander(f"🔬 Cribado Renal Pendiente - RAC ({len(tareas_cribado)} pacientes)"):
        st.write("Pacientes diabéticos o hipertensos sin analítica de albuminuria en los últimos 12 meses.")
        if not tareas_cribado:
            st.success("Todos los pacientes diana tienen su analítica al día.")
        else:
            for item in tareas_cribado[:5]:
                render_tarea_compacta(item)
            if len(tareas_cribado) > 5:
                st.info(f"Mostrando los 5 primeros. Quedan {len(tareas_cribado) - 5} más en la lista.")

except FileNotFoundError:
    st.error("No se encontraron los datos. Ejecuta 'python scripts/generate_dataset.py' primero.")