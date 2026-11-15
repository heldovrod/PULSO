import streamlit as st
import json
from pathlib import Path
from datetime import datetime

from models.paciente import PacienteFHIR
from core.risk_engine import evaluar, clave_orden
from core.clinical_rules import NIVELES

st.set_page_config(page_title="Seguimiento | PULSO", page_icon=":material/checklist:", layout="wide")

RUTA_PACIENTES = Path(__file__).parent.parent / "data" / "patients.json"
RUTA_SEGUIMIENTO = Path(__file__).parent.parent / "data" / "seguimiento.json"

# --- FUNCIONES DE PERSISTENCIA ---
def cargar_datos_seguimiento():
    if RUTA_SEGUIMIENTO.exists():
        with open(RUTA_SEGUIMIENTO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"estados": {}, "planes": {}, "fechas": {}}

def guardar_datos_seguimiento():
    datos = {
        "estados": st.session_state.estado_seguimiento,
        "planes": st.session_state.planes_medicos,
        "fechas": st.session_state.fechas_revision
    }
    with open(RUTA_SEGUIMIENTO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

# 1. CARGA DE PACIENTES
@st.cache_data
def cargar_pacientes_evaluados():
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

datos_evaluados = cargar_pacientes_evaluados()

if datos_evaluados is None:
    st.error("No se encontraron los datos.")
    st.stop()

# Inicializar estados de sesión
if "estado_seguimiento" not in st.session_state:
    db_seg = cargar_datos_seguimiento()
    st.session_state.estado_seguimiento = db_seg.get("estados", {})
    st.session_state.planes_medicos = db_seg.get("planes", {})
    st.session_state.fechas_revision = db_seg.get("fechas", {})

def obtener_estado(pid):
    return st.session_state.estado_seguimiento.get(pid, "Pendiente")

# Función global para guardar cambios
def guardar_cambio(pid, nuevo_estado, plan="", fecha=""):
    st.session_state.estado_seguimiento[pid] = nuevo_estado
    if plan: st.session_state.planes_medicos[pid] = plan
    if fecha: st.session_state.fechas_revision[pid] = fecha
    
    if nuevo_estado == "Pendiente":
        if pid in st.session_state.planes_medicos: del st.session_state.planes_medicos[pid]
        if pid in st.session_state.fechas_revision: del st.session_state.fechas_revision[pid]
        
    guardar_datos_seguimiento()
    st.cache_data.clear()
    st.rerun()

# ==========================================
# LÓGICA DE ENFOQUE VS VISTA GLOBAL
# ==========================================
if "paciente_seleccionado" in st.session_state and st.session_state.paciente_seleccionado:
    # --- MODO ENFOQUE: Un solo paciente ---
    id_buscado = st.session_state.paciente_seleccionado
    item = next((x for x in datos_evaluados if x["paciente"].id == id_buscado), None)
    
    if not item:
        st.error("Paciente no encontrado.")
        if st.button("Volver a la lista global"):
            st.session_state.paciente_seleccionado = None
            st.cache_data.clear()
            st.rerun()
        st.stop()
        
    p = item["paciente"]
    r = item["resultado"]
    estado_actual = obtener_estado(p.id)
    
    if st.button("← Volver al listado general", type="secondary"):
        st.session_state.paciente_seleccionado = None
        st.cache_data.clear()
        st.rerun()

    st.title(f":material/person: Seguimiento: {p.nombre}")
    st.caption(f"Edad: {p.edad} años | CIP: {p.id} | Riesgo: {r['categoria']}")

    with st.container(border=True):
        st.subheader(":material/assignment: Gestión del Caso")
        
        if r["alertas"] and estado_actual != "Revisado":
            st.markdown("**Alertas principales:**")
            for a in r["alertas"][:2]:
                st.error(f"**{a['tipo']}:** {a['texto']}", icon=":material/error:" if a['nivel']=="Grave" else ":material/warning:")
            st.divider()

        if estado_actual == "Pendiente":
            st.info("Este paciente está pendiente de valoración.")
            if st.button("Iniciar Seguimiento", icon=":material/play_arrow:", type="primary", use_container_width=True):
                guardar_cambio(p.id, "En seguimiento")
                
        elif estado_actual == "En seguimiento":
            st.warning("El paciente está en seguimiento activo.")
            
            with st.form("form_enfoque"):
                plan = st.text_input("Plan de actuación:", value=st.session_state.planes_medicos.get(p.id, ""))
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_rev = st.date_input("Fecha de revisión:")
                with col_f2:
                    hora_rev = st.time_input("Hora de la cita:", value=datetime.strptime("09:00", "%H:%M").time())
                
                sincronizar = st.checkbox("Sincronizar automáticamente con mi agenda clínica (Outlook / e-CAP)", value=True)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submit_revisado = st.form_submit_button("Marcar como Revisado", type="primary", use_container_width=True)
                with col_b:
                    submit_pendiente = st.form_submit_button("Cancelar y volver a Pendiente", use_container_width=True)

                if submit_revisado:
                    # 💡 VALIDACIÓN: Comprobamos si la hora está libre
                    db_seg_actual = cargar_datos_seguimiento()
                    fecha_hora_str = f"{fecha_rev.strftime('%Y-%m-%d')} {hora_rev.strftime('%H:%M')}"
                    
                    conflicto = False
                    for pid, f_str in db_seg_actual.get("fechas", {}).items():
                        if pid != p.id and f_str == fecha_hora_str:
                            conflicto = True
                            break
                    
                    if conflicto:
                        # 💡 AVISO: Bloqueamos la acción y pedimos al médico que cambie la hora
                        st.error(f"**Conflicto de agenda:** Ya tienes otro paciente programado para el {fecha_rev.strftime('%d/%m/%Y')} a las {hora_rev.strftime('%H:%M')}. Por favor, selecciona otra hora.", icon=":material/event_busy:")
                    else:
                        # Si no hay conflicto, guardamos
                        guardar_cambio(p.id, "Revisado", plan, fecha_hora_str)
                        if sincronizar: 
                            st.toast("Cita sincronizada correctamente en tu agenda.", icon=":material/calendar_month:")
                        else:
                            st.toast("Tarea guardada en PULSO.", icon=":material/save:")
                        
                if submit_pendiente:
                    guardar_cambio(p.id, "Pendiente")
                        
        elif estado_actual == "Revisado":
            st.success("El ciclo de seguimiento está cerrado.")
            st.write(f"**Plan aplicado:** {st.session_state.planes_medicos.get(p.id, 'No especificado')}")
            
            fecha_str = st.session_state.fechas_revision.get(p.id, "")
            if fecha_str:
                st.write(f"**Fecha de reevaluación:** {fecha_str}")
            
            if st.button("Reabrir Caso", icon=":material/replay:", use_container_width=True):
                guardar_cambio(p.id, "Pendiente")
                
    st.markdown("---")
    if st.button("Ver Ficha Clínica Completa", icon=":material/description:"):
        st.switch_page("views/5_FichaPaciente.py")

else:
    # --- VISTA GLOBAL (KANBAN) ---
    st.title(":material/checklist: Ciclo de Seguimiento Global")
    st.caption("Gestión de tareas, planes de actuación y reevaluación clínica")

    pendientes = [item for item in datos_evaluados if obtener_estado(item["paciente"].id) == "Pendiente"]
    en_seguimiento = [item for item in datos_evaluados if obtener_estado(item["paciente"].id) == "En seguimiento"]
    revisados = [item for item in datos_evaluados if obtener_estado(item["paciente"].id) == "Revisado"]

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(":material/groups: Analizados", len(datos_evaluados))
    col2.metric(":material/error: Prioritarios", sum(1 for x in datos_evaluados if x["resultado"]["categoria"] in ["Alto", "Muy alto"]))
    col3.metric(":material/hourglass_empty: Pendientes", len(pendientes))
    col4.metric(":material/check_circle: Finalizados", len(revisados))
    st.markdown("---")

    def render_tarjeta_global(item, estado_actual):
        p = item["paciente"]
        r = item["resultado"]
        
        with st.container(border=True):
            if estado_actual == "Revisado":
                c_info, c_plan, c_btn = st.columns([2.5, 6, 1.5], vertical_alignment="center")
                with c_info:
                    st.markdown(f"**{p.nombre}**")
                    st.caption(f"{p.edad} años | {p.id}")
                    st.markdown("<span style='background-color: #D1FAE5; color: #065F46; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>✅ Completado</span>", unsafe_allow_html=True)
                with c_plan:
                    plan_guardado = st.session_state.planes_medicos.get(p.id, "Sin plan registrado")
                    fecha_guardada = st.session_state.fechas_revision.get(p.id, "Sin fecha")
                    st.markdown(f"<span style='color: #374151; font-size: 0.9rem;'><b>Plan:</b> {plan_guardado}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 Reevaluación: {fecha_guardada}")
                with c_btn:
                    if st.button("Ver Ficha", key=f"f_{p.id}_rev", use_container_width=True, type="secondary", icon=":material/visibility:"):
                        st.session_state.paciente_seleccionado = p.id
                        st.switch_page("views/5_FichaPaciente.py")
            else:
                c_info, c_alerta, c_btn = st.columns([2.5, 6, 1.5], vertical_alignment="center")
                with c_info:
                    st.markdown(f"**{p.nombre}**")
                    st.caption(f"{p.edad} años | {p.id}")
                    if r["categoria"] == "Muy alto":
                        st.markdown("<span style='background-color: #FEE2E2; color: #991B1B; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>🔴 Muy alto</span>", unsafe_allow_html=True)
                    elif r["categoria"] == "Alto":
                        st.markdown("<span style='background-color: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;'>🟠 Alto</span>", unsafe_allow_html=True)
                with c_alerta:
                    if r["alertas"]:
                        alerta = r["alertas"][0]
                        st.error(f"**{alerta['tipo']}:** {alerta['texto']}", icon=":material/error:")
                with c_btn:
                    if st.button("Gestionar", key=f"f_{p.id}_{estado_actual}", use_container_width=True, type="primary" if estado_actual=="Pendiente" else "secondary", icon=":material/arrow_forward:"):
                        st.session_state.paciente_seleccionado = p.id
                        st.rerun()

    tab1, tab2, tab3 = st.tabs([
        f":material/hourglass_empty: Pendientes ({len(pendientes)})", 
        f":material/autorenew: En Seguimiento ({len(en_seguimiento)})", 
        f":material/check_circle: Revisados ({len(revisados)})"
    ])

    with tab1:
        if not pendientes: st.success("No hay pacientes pendientes de valoración.")
        else:
            for item in pendientes[:12]: render_tarjeta_global(item, "Pendiente")

    with tab2:
        if not en_seguimiento: st.info("No hay pacientes en seguimiento actualmente.")
        else:
            for item in en_seguimiento: render_tarjeta_global(item, "En seguimiento")

    with tab3:
        if not revisados: st.info("Aún no hay pacientes revisados.")
        else:
            for item in revisados: render_tarjeta_global(item, "Revisado")