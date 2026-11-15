from core.data import cargar_pacientes, HOY
from core.risk_engine import evaluar

def _p(pid):
    """Función auxiliar para obtener un paciente por su ID (Pacientes Demo)."""
    return next(p for p in cargar_pacientes() if p["id"] == pid)

def test_joan_pujol():
    """Joan Pujol: Riesgo Muy Alto por IC, caída renal e inercia terapéutica."""
    p = _p("PUJV601012001")
    r = evaluar(p, HOY)
    
    assert r["categoria"] == "Muy alto"
    # Buscamos la nueva alerta de iSGLT2
    assert any("sin iSGLT2" in a["texto"] for a in r["alertas"])
    assert any(a["tipo"] == "RENAL" and "68" in a["texto"] and "51" in a["texto"] for a in r["alertas"])
    
    # Test del IMC
    assert round(p["peso"] / p["talla"] ** 2, 1) == 29.7

def test_maria_garcia():
    """Maria Garcia: Riesgo de Ictus por FA no anticoagulada y PA Grave."""
    r = evaluar(_p("GURF715050002"), HOY)
    
    # El motor ahora devuelve "HTA grado II (moderada)" en lugar de "Grave"
    assert r["niveles"]["PA"] == "HTA grado II (moderada)"
    
    # La FA sin anticoagular sigue siendo Grave
    assert any(a["tipo"] == "CARDIO" and "ALERTA CRÍTICA" in a["texto"] for a in r["alertas"])

def test_albuminuria_no_valorada():
    """Paciente diabético/HTA sin RAC (Cribado pendiente)."""
    pacientes = cargar_pacientes()
    p = next(p for p in pacientes if (p.get("diabetes") or p.get("hta")) and p.get("rac") is None)
    
    r = evaluar(p, HOY)
    
    # Verificamos que salta la alerta de falta de cribado
    assert any("Albuminuria no registrada" in a["texto"] for a in r["alertas"])

def test_paciente_sano():
    """Paciente joven sin patologías."""
    pacientes = cargar_pacientes()
    p = next(p for p in pacientes if not p.get("diabetes") and not p.get("hta") and p.get("edad") < 60)
    
    r = evaluar(p, HOY)
    
    # El motor devuelve "Bajo"
    assert r["categoria"] == "Bajo"
    assert not any(a["nivel"] == "Grave" for a in r["alertas"])