import streamlit as st
import json
from pathlib import Path
from datetime import datetime

from core.risk_engine import evaluar

# 1. Configuración de la página (Debe ir al principio)
st.set_page_config(page_title="Ficha del Paciente", layout="wide")

# Mapeo de objetivos de LDL 
OBJETIVO_LDL_MAP = {
    "Muy alto": 55,
    "Alto": 70,
    "Moderado": 100,
    "Bajo": 116
}

def mostrar_ficha(paciente, resultado_motor):
    # 1. CABECERA (Ajustamos columnas para que no se corte el texto)
    col1, col2 = st.columns([2.5, 1.5])
    
    with col1:
        st.header(f":material/person: {paciente.get('nombre', 'Desconocido')}")
        st.caption(f"Edad: {paciente.get('edad', '-')} años | CIP: {paciente.get('id', '-')} | Sexo: {paciente.get('sexo', '-')}")
        
        # Calculamos el Score de Riesgo
        base_score = {"Bajo": 0, "Moderado": 20, "Alto": 40, "Muy alto": 60}
        score = base_score.get(resultado_motor["categoria"], 0)
        for a in resultado_motor["alertas"]:
            if a["nivel"] == "Grave": score += 10
            elif a["nivel"] == "Moderado": score += 5
            elif a["nivel"] == "Leve": score += 2
        score = min(100, score)
        
        if score >= 80:
            st.markdown(f":red[**SCORE DE RIESGO: {score} / 100**] &nbsp;·&nbsp; Acción inmediata recomendada")
        elif score >= 50:
            st.markdown(f":orange[**SCORE DE RIESGO: {score} / 100**] &nbsp;·&nbsp; Requiere seguimiento")
        else:
            st.markdown(f":green[**SCORE DE RIESGO: {score} / 100**] &nbsp;·&nbsp; Paciente controlado")
        
    with col2:
        st.metric(
            label="RIESGO CV", 
            value=resultado_motor["categoria"], 
            delta="Riesgo Crítico" if resultado_motor["categoria"] == "Muy alto" else "",
            delta_color="inverse" 
        )
        if st.button("Ver Análisis Clínico", use_container_width=True):
            st.session_state.paciente_seleccionado = paciente.get("id")
            st.switch_page("views/2_Dashboard.py")

    st.markdown("---")
    
    # 2. PESTAÑAS DE DETALLE
    tab1, tab2, tab3 = st.tabs([
        ":material/analytics: Resumen Clínico", 
        ":material/assignment: Plan de Seguimiento", 
        ":material/engineering: Transparencia"
    ])
    
    # --- PESTAÑA 1: RESUMEN CLÍNICO ---
    with tab1:
        # Fila 1: PA, eGFR, IMC
        c1, c2, c3 = st.columns(3)
        
        # Comentario visual en la PA (Muestra si es Normal, HTA grado I, II...)
        with c1:
            tomas = paciente.get('pa_tomas', [])
            ultima_pa = f"{tomas[-1][0]}/{tomas[-1][1]} mmHg" if tomas else "Sin datos"
            nivel_pa = resultado_motor['niveles'].get('PA', 'Desconocido')
            st.container(border=True).metric(
                label="PRESIÓN ARTERIAL (PA)", 
                value=ultima_pa,
                delta=nivel_pa,
                delta_color="inverse" if "Normal" not in nivel_pa and "Óptima" not in nivel_pa else "normal"
            )
            
        with c2:
            egfr = paciente.get('egfr')
            st.container(border=True).metric(
                label="FUNCIÓN RENAL (eGFR)", 
                value=f"{egfr} mL/min" if egfr is not None else "Sin datos"
            )
            
        # Comentario visual en el IMC (Muestra si es Normopeso, Sobrepeso u Obesidad)
        with c3:
            peso, talla = paciente.get("peso"), paciente.get("talla")
            if peso and talla:
                imc = round(peso / (talla ** 2), 1)
                cat_imc = "Obesidad" if imc >= 30 else ("Sobrepeso" if imc >= 25 else "Normopeso")
                st.container(border=True).metric(
                    label="COMPOSICIÓN CORPORAL", 
                    value=f"{imc} IMC",
                    delta=cat_imc,
                    delta_color="inverse" if cat_imc != "Normopeso" else "normal"
                )
            else:
                st.container(border=True).metric(label="COMPOSICIÓN CORPORAL", value="Sin datos")

        # Fila 2: LDL, HbA1c, RAC
        st.markdown("<br>", unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        with c4:
            ldl = paciente.get('ldl')
            objetivo = OBJETIVO_LDL_MAP.get(resultado_motor["categoria"], 100)
            st.container(border=True).metric(label="COLESTEROL LDL", value=f"{ldl} mg/dL" if ldl is not None else "Sin datos", delta=f"Objetivo <{objetivo}" if ldl is not None else None, delta_color="inverse" if ldl is not None and ldl > objetivo else "normal")
        with c5:
            hba1c = paciente.get('hba1c')
            st.container(border=True).metric(label="HEMOGLOBINA GLICOSILADA", value=f"{hba1c} %" if hba1c is not None else "No medida")
        with c6:
            rac = paciente.get('rac')
            st.container(border=True).metric(label="ALBUMINURIA (RAC)", value=f"{rac} mg/g" if rac is not None else "No medido", delta="Pendiente cribado" if rac is None else "Medido", delta_color="inverse" if rac is None else "normal")

        st.markdown("---")
        
        st.subheader("Alertas Clínicas")
        if not resultado_motor["alertas"]:
            st.success("No se han detectado alertas graves para este paciente.", icon=":material/check_circle:")
        else:
            alertas_ord = sorted(resultado_motor["alertas"], key=lambda x: {"Grave":3, "Moderado":2, "Leve":1}.get(x["nivel"], 0), reverse=True)
            for alerta in alertas_ord:
                if alerta["nivel"] == "Grave":
                    st.error(f"**{alerta['tipo']}:** {alerta['texto']}", icon=":material/error:")
                elif alerta["nivel"] == "Moderado":
                    st.warning(f"**{alerta['tipo']}:** {alerta['texto']}", icon=":material/warning:")
                else:
                    st.info(f"**{alerta['tipo']}:** {alerta['texto']}", icon=":material/info:")

    # --- PESTAÑA 2: ESTADO DEL SEGUIMIENTO ---
    with tab2:
        RUTA_SEG = Path(__file__).parent.parent / "data" / "seguimiento.json"
        if RUTA_SEG.exists():
            with open(RUTA_SEG, "r", encoding="utf-8") as f:
                db_seg = json.load(f)
        else:
            db_seg = {"estados": {}, "planes": {}, "fechas": {}}
            
        estado_actual = db_seg["estados"].get(paciente["id"], "Pendiente")
        
        with st.container(border=True):
            st.subheader(":material/assignment: Estado del Seguimiento")
            
            if estado_actual == "Pendiente":
                st.info("Este paciente está pendiente de valoración médica.")
            elif estado_actual == "En seguimiento":
                st.warning("Este paciente está en seguimiento activo.")
                plan_guardado = db_seg["planes"].get(paciente["id"], "No especificado")
                st.markdown(f"**Plan actual:** {plan_guardado}")
            elif estado_actual == "Revisado":
                st.success("Seguimiento cerrado. El paciente ha sido revisado.")
                plan_guardado = db_seg["planes"].get(paciente["id"], "No especificado")
                st.markdown(f"**Plan clínico aplicado:** {plan_guardado}")

            st.divider()
            
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b2:
                if st.button("Gestionar en Seguimiento", type="primary", use_container_width=True, icon=":material/arrow_forward:"):
                    st.session_state.paciente_seleccionado = paciente.get("id")
                    st.switch_page("views/6_Seguimiento.py")

    # --- PESTAÑA 3: TRANSPARENCIA ---
    with tab3:
        st.write("### Trazabilidad Clínica")
        st.write("- **Guías aplicadas:** ESH 2023 (Tensión), KDIGO (Renal), ESC 2024 (FA y Lípidos).")
        st.write("- **Datos procesados:** Analítica, antecedentes, medicación y constantes de los últimos 12 meses.")
        st.json(resultado_motor)

# ==========================================
# LÓGICA DE EJECUCIÓN
# ==========================================
ruta_datos = Path(__file__).parent.parent / "data" / "patients.json"

try:
    with open(ruta_datos, "r", encoding="utf-8") as f:
        pacientes = json.load(f)
    
    if "paciente_seleccionado" in st.session_state:
        id_buscado = st.session_state.paciente_seleccionado
        paciente_demo = next((p for p in pacientes if p["id"] == id_buscado), pacientes[0])
    else:
        paciente_demo = next((p for p in pacientes if p["id"] == "PUJV601012001"), pacientes[0])
    
    hoy = datetime(2026, 11, 14)
    resultado = evaluar(paciente_demo, hoy)
    mostrar_ficha(paciente_demo, resultado)

except FileNotFoundError:
    st.error("No se encuentra el archivo patients.json. Ejecuta primero generate_dataset.py")
except Exception as e:
    st.error(f"Error inesperado al cargar la ficha: {e}")
