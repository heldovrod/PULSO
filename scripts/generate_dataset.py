import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

RUTA_DATOS = Path(__file__).parent.parent / "data" / "patients.json"
HOY = datetime(2026, 11, 14)

def generar_pacientes(total=250):
    pacientes = []
    
    # ==========================================
    # 1. PACIENTES DEMO (HÉROE)
    # ==========================================
    
    # Demo 1: Joan Pujol (Riesgo Muy Alto, Caída Renal Silenciosa, Inercia Terapéutica)
    pacientes.append({
        "id": "PUJV601012001",
        "nombre": "Joan Pujol Vila",
        "edad": 64,
        "sexo": "hombre",
        "peso": 88.0,
        "talla": 1.72,
        "diabetes": True,
        "hta": True,
        "antecedentes": {
            "infarto": False, "ictus_ait": False, "arteriopatia": False, 
            "insuficiencia_cardiaca": True, "revascularizacion": False
        },
        "pa_tomas": [[150, 90], [152, 91], [154, 92]], 
        "egfr": 51,
        "rac": 350,
        "ldl": 142,
        "hba1c": 7.8,                
        "adherencia_baja": False,    
        "ecg": {
            "ritmo": "extrasistoles",
            "arritmia_ventricular_sostenida": False, "bloqueo_av_avanzado": False,
            "qt_largo": False, "anticoagulado": False, "fc_reposo": 78
        },
        # 💡 NUEVO: Añadimos simvastatina y amiodarona para que salte la alerta de rabdomiólisis
        # Falla iSGLT2 a propósito
        "medicacion": ["metformina", "simvastatina", "amiodarona"], 
        "series": {
            "egfr": [
                [(HOY - timedelta(days=300)).strftime("%Y-%m-%d"), 68.0],
                [(HOY - timedelta(days=10)).strftime("%Y-%m-%d"), 51.0],
                [HOY.strftime("%Y-%m-%d"), 51.0]
            ]
        }
    })

    # Demo 2: Maria Garcia (Riesgo Alto de Ictus por FA no tratada)
    pacientes.append({
        "id": "GURF715050002",
        "nombre": "Maria Garcia Font",
        "edad": 71,
        "sexo": "mujer",
        "peso": 68.5,
        "talla": 1.60,
        "diabetes": False,
        "hta": True,
        "antecedentes": {
            "infarto": False, "ictus_ait": False, "arteriopatia": False, 
            "insuficiencia_cardiaca": False, "revascularizacion": False
        },
        "pa_tomas": [[158, 94], [160, 95], [162, 96]],
        "egfr": 64,
        "rac": 15,
        "ldl": 155,
        "hba1c": None,              
        "adherencia_baja": False,   
        "ecg": {
            "ritmo": "FA",
            "arritmia_ventricular_sostenida": False, "bloqueo_av_avanzado": False,
            "qt_largo": False, "anticoagulado": False, "fc_reposo": 115 
        },
        "medicacion": ["antiagregante"], # Error grave: necesita anticoagulante
        "series": {
            "egfr": [
                [(HOY - timedelta(days=200)).strftime("%Y-%m-%d"), 66.0],
                [(HOY - timedelta(days=5)).strftime("%Y-%m-%d"), 64.0],
                [HOY.strftime("%Y-%m-%d"), 64.0] 
            ]
        }
    })

    # ==========================================
    # 2. GENERACIÓN POR ARQUETIPOS CLÍNICOS REALISTAS
    # ==========================================
    
    nombres_h = ["Carlos", "Miguel", "Antonio", "Francisco", "Jose", "David", "Javier", "Daniel"]
    nombres_m = ["Laura", "Carmen", "Ana", "Isabel", "Dolores", "Marta", "Elena", "Sofia"]
    apellidos = ["Garcia", "Martinez", "Lopez", "Sanchez", "Perez", "Gomez", "Ruiz", "Vidal", "Serra", "Costa"]

    for i in range(total - 2):
        # Pesos basados en epidemiología real española
        arquetipo = random.choices(
            ["Sano", "Hipertenso", "Diabetico", "Cardiopata_Grave"], 
            weights=[50, 30, 15, 5]
        )[0]
        
        sexo = random.choice(["hombre", "mujer"])
        nombre = random.choice(nombres_h) if sexo == "hombre" else random.choice(nombres_m)
        apell = f"{random.choice(apellidos)} {random.choice(apellidos)}"
        
        # Plantilla base vacía
        paciente = {
            "id": f"CIP{str(uuid.uuid4().int)[:9]}", 
            "nombre": f"{nombre} {apell}",
            "sexo": sexo,
            "peso": None,
            "talla": None,
            "hba1c": None,
            "adherencia_baja": False,
            "antecedentes": {"infarto": False, "ictus_ait": False, "arteriopatia": False, "insuficiencia_cardiaca": False, "revascularizacion": False},
            "ecg": {"ritmo": "Normal", "arritmia_ventricular_sostenida": False, "bloqueo_av_avanzado": False, "qt_largo": False, "anticoagulado": False, "fc_reposo": 70},
            "series": {"egfr": []},
            "medicacion": []
        }

        if arquetipo == "Sano":
            paciente.update({
                "edad": random.randint(30, 55),
                "peso": round(random.uniform(60.0, 80.0), 1),  
                "talla": round(random.uniform(1.60, 1.85), 2), 
                "diabetes": False, "hta": False,
                "pa_tomas": [[random.randint(110, 125), random.randint(70, 80)], [random.randint(110, 125), random.randint(70, 80)]],
                "egfr": round(random.uniform(90, 120), 1),
                "rac": random.randint(2, 15),
                "ldl": random.randint(70, 110)
            })
            paciente["series"]["egfr"] = [
                [(HOY - timedelta(days=200)).strftime("%Y-%m-%d"), paciente["egfr"] + random.uniform(-2, 2)],
                [HOY.strftime("%Y-%m-%d"), paciente["egfr"]]
            ]
            
        elif arquetipo == "Hipertenso":
            paciente.update({
                "edad": random.randint(50, 75),
                "peso": round(random.uniform(70.0, 92.0), 1),  
                "talla": round(random.uniform(1.55, 1.80), 2), 
                "diabetes": False, "hta": True,
                "pa_tomas": [[random.randint(130, 145), random.randint(80, 90)], [random.randint(125, 135), random.randint(75, 85)]],
                "egfr": round(random.uniform(70, 95), 1),
                # 30% de los hipertensos no tienen RAC medido
                "rac": random.randint(10, 25) if random.random() < 0.7 else None,
                "ldl": random.randint(90, 130),
                "medicacion": ["antihipertensivo"]
            })
            paciente["series"]["egfr"] = [
                [(HOY - timedelta(days=250)).strftime("%Y-%m-%d"), paciente["egfr"] + random.uniform(0, 4)],
                [HOY.strftime("%Y-%m-%d"), paciente["egfr"]]
            ]

        elif arquetipo == "Diabetico":
            # Solo el 30% de los diabéticos desarrollan ERC (eGFR bajo)
            tiene_erc = random.random() < 0.3
            
            paciente.update({
                "edad": random.randint(55, 80),
                "peso": round(random.uniform(75.0, 100.0), 1),
                "talla": round(random.uniform(1.55, 1.80), 2), 
                "diabetes": True, 
                "hta": random.random() < 0.7, # 70% de los diabéticos son hipertensos
                "pa_tomas": [[random.randint(135, 155), random.randint(80, 95)], [random.randint(130, 150), random.randint(80, 95)]],
                "egfr": round(random.uniform(50, 75), 1) if tiene_erc else round(random.uniform(80, 110), 1),
                # Si tienen ERC, un 50% no tiene RAC. Si no tienen ERC, el RAC suele ser normal.
                "rac": (random.randint(30, 300) if random.random() < 0.5 else None) if tiene_erc else random.randint(2, 20),
                "ldl": random.randint(100, 150),
                "medicacion": random.sample(["metformina", "estatina", "iSGLT2", "antihipertensivo"], k=random.randint(2, 3))
            })
            
            # Caída de eGFR realista solo si tienen ERC
            if tiene_erc:
                paciente["series"]["egfr"] = [
                    [(HOY - timedelta(days=300)).strftime("%Y-%m-%d"), paciente["egfr"] + random.uniform(2, 6)],
                    [HOY.strftime("%Y-%m-%d"), paciente["egfr"]] 
                ]
            else:
                paciente["series"]["egfr"] = [
                    [(HOY - timedelta(days=200)).strftime("%Y-%m-%d"), paciente["egfr"] + random.uniform(-2, 2)],
                    [HOY.strftime("%Y-%m-%d"), paciente["egfr"]] 
                ]

        elif arquetipo == "Cardiopata_Grave":
            paciente.update({
                "edad": random.randint(65, 90),
                "peso": round(random.uniform(65.0, 95.0), 1),  
                "talla": round(random.uniform(1.55, 1.78), 2), 
                "diabetes": random.random() > 0.5, "hta": True,
                "pa_tomas": [[random.randint(140, 170), random.randint(85, 100)], [random.randint(145, 175), random.randint(90, 105)]],
                "egfr": round(random.uniform(25, 50), 1),
                "rac": random.randint(50, 500),
                "ldl": random.randint(120, 180),
                "medicacion": random.sample(["estatina", "anticoagulante", "beta-bloqueante", "diuretico"], k=random.randint(2, 4))
            })
            paciente["antecedentes"]["infarto"] = random.random() > 0.5
            paciente["antecedentes"]["insuficiencia_cardiaca"] = random.random() > 0.4 # 60% tienen IC
            
            if random.random() > 0.5:
                paciente["ecg"]["ritmo"] = "FA"
                paciente["ecg"]["anticoagulado"] = "anticoagulante" in paciente["medicacion"]
                paciente["ecg"]["fc_reposo"] = random.randint(80, 120)
            
            paciente["series"]["egfr"] = [
                [(HOY - timedelta(days=180)).strftime("%Y-%m-%d"), paciente["egfr"] + random.uniform(1, 5)],
                [HOY.strftime("%Y-%m-%d"), paciente["egfr"]] 
            ]

        # Simular fallo del sistema (RAC no medido) de forma global
        if (paciente.get("diabetes") or paciente.get("hta")) and paciente.get("rac") is not None:
            if random.random() > 0.6:
                paciente["rac"] = None

        # Simular algunos datos ausentes (5% probabilidad) para probar la robustez de Pydantic
        if random.random() > 0.95:
            paciente["egfr"] = None
            paciente["ldl"] = None
            if len(paciente["series"]["egfr"]) > 0 and paciente["series"]["egfr"][-1][0] == HOY.strftime("%Y-%m-%d"):
                paciente["series"]["egfr"].pop()
        
        # 1. Añadir HbA1c a los diabéticos
        if paciente.get("diabetes"):
            paciente["hba1c"] = round(random.uniform(6.5, 10.5), 1)
        elif random.random() > 0.8:
            paciente["hba1c"] = round(random.uniform(5.5, 6.9), 1)

        # 2. Simular falta de adherencia
        if paciente.get("hta") and random.random() > 0.85:
            paciente["adherencia_baja"] = True

        # 3. Simular errores graves de medicación (Seguridad Farmacológica)
        # Doble bloqueo del SRAA (IECA + ARA-II)
        if random.random() > 0.90:
            paciente["medicacion"].extend(["enalapril", "losartan"])
            
        # Simvastatina + Amiodarona (Riesgo de rabdomiólisis)
        if random.random() > 0.90:
            paciente["medicacion"].extend(["simvastatina", "amiodarona"])

        # Triple Whammy (AINE + IECA + Diurético)
        if random.random() > 0.90:
            paciente["medicacion"].extend(["ibuprofeno", "enalapril", "furosemida"])

        # Simvastatina + Gemfibrozil
        if random.random() > 0.90:
            paciente["medicacion"].extend(["simvastatina", "gemfibrozil"])

        pacientes.append(paciente)

    # 3. GUARDAR EL ARCHIVO JSON
    RUTA_DATOS.parent.mkdir(exist_ok=True, parents=True)
    with open(RUTA_DATOS, "w", encoding="utf-8") as f:
        json.dump(pacientes, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Se han generado {len(pacientes)} pacientes realistas basados en epidemiología.")
    print(f"✅ Guardado en: {RUTA_DATOS}")

if __name__ == "__main__":
    generar_pacientes()