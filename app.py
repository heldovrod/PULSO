import streamlit as st
from pathlib import Path

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(
    page_title="PULSO", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

ruta_css = Path(__file__).parent / "assets" / "style.css"
if ruta_css.exists():
    local_css(ruta_css)

# 1. Definir Páginas
agenda = st.Page("views/1_Agenda.py", title="Agenda diaria", icon=":material/calendar_today:", default=True)
semanal = st.Page("views/3_PanelSemanal.py", title="Oportunidades Preventivas", icon=":material/lightbulb:")
prioritarios = st.Page("views/4_PacientesPrioritarios.py", title="Pacientes prioritarios", icon=":material/groups:")
ficha = st.Page("views/5_FichaPaciente.py", title="Ficha de paciente", icon=":material/person:")
seguimiento = st.Page("views/6_Seguimiento.py", title="Seguimiento", icon=":material/checklist:")
dashboard = st.Page("views/2_Dashboard.py", title="Dashboard", icon=":material/dashboard:")

# 2. Navegación
pg = st.navigation([agenda, prioritarios, semanal, ficha, seguimiento, dashboard])

# 3. Perfil del médico en la parte inferior del Sidebar
st.sidebar.markdown("""
    <div class='user-profile-bottom'>
        <div style='display: flex; align-items: center; gap: 15px;'>
            <div style='background-color: #005B8F; color: white; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;'>
                CM
            </div>
            <div>
                <div style='color: #FFFFFF; font-weight: 600; font-size: 1rem;'>Dra. Carmen M.</div>
                <div style='color: #94A3B8; font-size: 0.8rem;'>Atención Primaria - CAP Nord</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 4. Ejecutar vista
pg.run()
