[Ver repositorio en GitHub](https://github.com/HackathonBoehringerIT/Ciclosporinas)

# PULSO - Priorización Unificada para el Liderazgo en Salud y Organoprotección

**PULSO** es una herramienta de soporte a la decisión clínica diseñada para la Atención Primaria. Su objetivo es detectar de forma precoz el riesgo cardiovascular y renal, priorizar a los pacientes que necesitan atención inmediata y facilitar la toma de decisiones médicas, todo ello sin incrementar la carga administrativa.

Este proyecto ha sido desarrollado para el **Hackathon Boehringer Ingelheim 2026 (Reto 1)**.

---

## El Problema
En el día a día de un médico de familia (como la Dra. Carmen M.), la información está fragmentada. Un paciente puede tener una analítica "aceptable" pero esconder una albuminuria no valorada o una función renal que se deteriora silenciosamente. El tiempo por consulta es limitado y es imposible revisar manualmente a los cientos de pacientes del cupo.

## La Solución
Hemos creado una aplicación web interactiva (Streamlit) que simula un sistema integrado con el e-CAP (mediante un adaptador FHIR). El sistema evalúa automáticamente a todo el cupo de pacientes y genera alertas clínicas accionables basadas en guías oficiales (ESC, KDIGO, ESH).

### Funcionalidades Principales:
1. **Motor Clínico (`risk_engine.py`):** Evalúa el riesgo cardiovascular global, detecta inercias terapéuticas, errores de medicación (ej. Triple Whammy) y oportunidades de cribado.
2. **Agenda Diaria:** Muestra a los pacientes citados para hoy, destacando visualmente sus alertas clínicas antes de que entren por la puerta.
3. **Directorio de Prioritarios:** Ranking de pacientes según su nivel de riesgo, con filtros dinámicos.
4. **Ficha del Paciente:** Resumen ejecutivo con métricas clave (eGFR, PA, IMC, LDL, RAC), alertas clínicas y un score de riesgo visual.
5. **Seguimiento (Kanban):** Permite gestionar el ciclo del paciente (Pendiente → En seguimiento → Revisado), programar reevaluaciones y simular la sincronización con la agenda médica.
6. **Transparencia del Algoritmo:** Una pestaña dedicada a mostrar las guías aplicadas y el JSON de salida, demostrando que la herramienta no es una "caja negra".

---

## Tecnologías Utilizadas
*   **Python** (Lógica clínica y backend)
*   **Streamlit** (Interfaz de usuario)
*   **Pydantic** (Validación de datos clínicos y modelo FHIR)
*   **Plotly** (Gráficos interactivos de evolución clínica)
*   **JSON** (Simulación de base de datos persistente)

---

## Cómo ejecutar el proyecto en local

1. Clona este repositorio:
   ```bash
   git clone https://github.com/HackathonBoehringerIT/Ciclosporinas.git
   cd Ciclosporinas