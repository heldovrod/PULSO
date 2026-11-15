from datetime import datetime

OBJETIVO_LDL = {
    "Muy alto": 55,
    "Alto": 70,
    "Moderado": 100,
    "Bajo": 116
}

RANGO_RIESGO = {"Bajo": 0, "Moderado": 1, "Alto": 2, "Muy alto": 3}

def evaluar(paciente_dict, fecha_evaluacion=None):
    if fecha_evaluacion is None:
        fecha_evaluacion = datetime.now()
        
    alertas = []
    categoria_riesgo = "Bajo"
    niveles = {"PA": "Normal", "LDL": "Normal", "eGFR": "Normal", "HbA1c": "Normal"}
    
    # 1. EVALUACIÓN DE TENSIÓN ARTERIAL
    if paciente_dict.get("pa_tomas"):
        tomas = paciente_dict["pa_tomas"]
        ultima_pa = tomas[-1]
        sys, dia = ultima_pa[0], ultima_pa[1]
        
        if sys >= 180 or dia >= 110:
            niveles["PA"] = "HTA grado III (grave)"
            alertas.append({"tipo": "CARDIO", "nivel": "Grave", "texto": f"HTA grado III: {sys}/{dia} mmHg"})
            categoria_riesgo = max(categoria_riesgo, "Alto", key=RANGO_RIESGO.get)
        elif sys >= 160 or dia >= 100:
            niveles["PA"] = "HTA grado II (moderada)"
            alertas.append({"tipo": "CARDIO", "nivel": "Moderado", "texto": f"HTA grado II: {sys}/{dia} mmHg"})
        elif sys >= 140 or dia >= 90:
            niveles["PA"] = "HTA grado I (leve)"
        
        # Inercia Terapéutica
        if len(tomas) >= 2:
            penultima_pa = tomas[-2]
            if (sys >= 140 or dia >= 90) and (penultima_pa[0] >= 140 or penultima_pa[1] >= 90):
                if sys >= 160 or dia >= 100 or penultima_pa[0] >= 160 or penultima_pa[1] >= 100:
                    alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "Inercia terapéutica HTA. Dos visitas con PA ≥160/100. Se requiere cambio de tratamiento."})
                else:
                    alertas.append({"tipo": "MEDICACIÓN", "nivel": "Moderado", "texto": "Inercia terapéutica HTA. Dos visitas con PA ≥140/90. Valorar ajuste."})

    # 2. EVALUACIÓN METABÓLICA (LDL y HbA1c)
    ldl = paciente_dict.get("ldl")
    hba1c = paciente_dict.get("hba1c")
    
    if ldl is not None:
        if ldl >= 190:
            niveles["LDL"] = "Muy alto (≥190)"
            alertas.append({"tipo": "METABÓLICO", "nivel": "Grave", "texto": f"LDL {ldl} mg/dL (≥190). Sospecha de hipercolesterolemia familiar."})
            categoria_riesgo = max(categoria_riesgo, "Alto", key=RANGO_RIESGO.get)
        elif ldl > OBJETIVO_LDL.get(categoria_riesgo, 116) + 50:
            niveles["LDL"] = "Grave por exceso"
            alertas.append({"tipo": "METABÓLICO", "nivel": "Grave", "texto": f"LDL {ldl} mg/dL muy por encima del objetivo ({OBJETIVO_LDL.get(categoria_riesgo)} mg/dL)."})
        elif ldl > OBJETIVO_LDL.get(categoria_riesgo, 116):
            niveles["LDL"] = "Moderado por exceso"
            alertas.append({"tipo": "METABÓLICO", "nivel": "Moderado", "texto": f"LDL {ldl} mg/dL por encima del objetivo ({OBJETIVO_LDL.get(categoria_riesgo)} mg/dL)."})

    if hba1c is not None:
        if hba1c >= 10.0:
            niveles["HbA1c"] = "Grave"
            alertas.append({"tipo": "METABÓLICO", "nivel": "Grave", "texto": f"Descontrol metabólico grave (HbA1c {hba1c}%)."})
        elif hba1c >= 8.0:
            niveles["HbA1c"] = "Moderado"
            alertas.append({"tipo": "METABÓLICO", "nivel": "Moderado", "texto": f"Inercia terapéutica en diabetes (HbA1c {hba1c}%)."})

    # 3. EVALUACIÓN DE RIESGO CRÓNICO Y LESIÓN DE ÓRGANO
    antecedentes = paciente_dict.get("antecedentes", {})
    egfr = paciente_dict.get("egfr")
    rac = paciente_dict.get("rac")
    diabetes = paciente_dict.get("diabetes", False)
    
    mrc_avanzada = egfr is not None and egfr < 30
    lesion_organo = (egfr is not None and egfr < 60) or (rac is not None and rac >= 30)
    
    if antecedentes.get("infarto") or antecedentes.get("ictus_ait") or antecedentes.get("arteriopatia"):
        categoria_riesgo = max(categoria_riesgo, "Muy alto", key=RANGO_RIESGO.get)
    elif (diabetes and lesion_organo) or mrc_avanzada:
        categoria_riesgo = max(categoria_riesgo, "Muy alto", key=RANGO_RIESGO.get)
    elif diabetes or (egfr is not None and 30 <= egfr <= 59):
        categoria_riesgo = max(categoria_riesgo, "Alto", key=RANGO_RIESGO.get)

    # TENDENCIA eGFR (KDIGO)
    serie_egfr = paciente_dict.get("series", {}).get("egfr", [])
    if len(serie_egfr) >= 2:
        serie_ordenada = sorted(serie_egfr, key=lambda x: x[0])
        val_inicial = serie_ordenada[0][1]
        val_final = serie_ordenada[-1][1]
        if val_inicial is not None and val_final is not None:
            if val_inicial - val_final >= 5:
                alertas.append({"tipo": "RENAL", "nivel": "Moderado", "texto": f"Progresión rápida de la enfermedad renal (eGFR de {val_inicial} a {val_final})."})
    
    # 3.5. ALGORITMO CORRECTOR: FALTA DE TRATAMIENTO NEFROPROTECTOR
    if diabetes and lesion_organo and "isglt2" not in [m.lower() for m in paciente_dict.get("medicacion", [])]:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Moderado", "texto": "DM2 + MRC sin iSGLT2. Valorar inicio de tratamiento nefroprotector."})


    # 4. SEGURIDAD FARMACOLÓGICA
    meds = [m.lower() for m in paciente_dict.get("medicacion", [])]
    
    tiene_ieca = any("enalapril" in m or "captopril" in m for m in meds)
    tiene_araii = any("losartan" in m or "valsartan" in m for m in meds)
    tiene_arni = any("sacubitril" in m for m in meds)
    
    if tiene_ieca and tiene_arni:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "CONTRAINDICACIÓN: IECA + sacubitril/valsartán. Riesgo de angioedema."})
    if tiene_ieca and tiene_araii:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "CONTRAINDICACIÓN: Posible bloqueo doble del SRAA (IECA + ARA-II)."})
        
    tiene_sildenafilo = any("sildenafilo" in m for m in meds)
    tiene_riociguat = any("riociguat" in m for m in meds)
    if tiene_sildenafilo and tiene_riociguat:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "CONTRAINDICACIÓN: Sildenafilo + riociguat. Riesgo de hipotensión sintomática grave."})
        
    tiene_bisoprolol = any("bisoprolol" in m for m in meds)
    tiene_verapamil = any("verapamil" in m or "diltiazem" in m for m in meds)
    if tiene_bisoprolol and tiene_verapamil:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "Riesgo de bradicardia/bloqueo AV: Betabloqueante + Verapamil/Diltiazem."})
        
    tiene_metformina = any("metformina" in m for m in meds)
    if tiene_metformina and egfr is not None and egfr < 30:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "CONTRAINDICACIÓN: Metformina con eGFR < 30. Riesgo de acidosis láctica. Suspender inmediatamente."})
        
    tiene_simvastatina = any("simvastatina" in m for m in meds)
    tiene_amiodarona = any("amiodarona" in m for m in meds)
    tiene_gemfibrozil = any("gemfibrozil" in m for m in meds)

    # Simvastatina + Amiodarona (Nuevo texto con dosis y alternativa)
    if tiene_simvastatina and tiene_amiodarona:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "CONTRAINDICACIÓN: Simvastatina + Amiodarona. Riesgo de miopatía y rabdomiólisis. No superar los 20 mg/día de simvastatina. Valorar cambio a pravastatina o rosuvastatina."})

    # Simvastatina + Gemfibrozil
    if tiene_simvastatina and tiene_gemfibrozil:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "CONTRAINDICACIÓN: Simvastatina + Gemfibrozil. Riesgo muy elevado de miopatía y rabdomiólisis. Evitar la combinación y valorar un fibrato alternativo como el fenofibrato."})
        
    tiene_aine = any("ibuprofeno" in m or "naproxeno" in m or "diclofenaco" in m for m in meds)
    tiene_diuretico = any("hidroclorotiazida" in m or "furosemida" in m for m in meds)
    if tiene_aine and (tiene_ieca or tiene_araii) and tiene_diuretico:
        alertas.append({"tipo": "MEDICACIÓN", "nivel": "Grave", "texto": "TRIPLE WHAMMY: AINE + IECA/ARA-II + Diurético. Riesgo muy elevado de fracaso renal agudo. Retirar el AINE."})
        
    if (egfr is not None and egfr < 30) or (rac is not None and rac >= 300):
        alertas.append({"tipo": "RENAL", "nivel": "Grave", "texto": "Criterio de derivación a Nefrología: eGFR < 30 o RAC ≥ 300. Valorar derivación."})
    
    # 5. ADHERENCIA
    if paciente_dict.get("adherencia_baja") is True:
        alertas.append({"tipo": "FARMACIA", "nivel": "Grave", "texto": "ALERTA ADHERENCIA: El paciente no está retirando la medicación de la farmacia."})
        categoria_riesgo = max(categoria_riesgo, "Muy alto", key=RANGO_RIESGO.get)

    # 6. ECG Y ARRITMIAS
    ecg = paciente_dict.get("ecg", {})
    if ecg.get("ritmo") == "FA":
        puntos = 0
        if antecedentes.get("insuficiencia_cardiaca"): puntos += 1
        if paciente_dict.get("hta"): puntos += 1
        if paciente_dict.get("edad") >= 75: puntos += 2
        elif paciente_dict.get("edad") >= 65: puntos += 1
        if diabetes: puntos += 1
        if antecedentes.get("ictus_ait"): puntos += 2
        if antecedentes.get("infarto") or antecedentes.get("arteriopatia"): puntos += 1
        if paciente_dict.get("sexo", "H") == "M": puntos += 1
        
        anticoagulado = ecg.get("anticoagulado", False)
        
        if not anticoagulado:
            umbral = 3 if paciente_dict.get("sexo", "H") == "M" else 2
            if puntos >= umbral:
                alertas.append({"tipo": "CARDIO", "nivel": "Grave", "texto": "ALERTA CRÍTICA: Paciente con FA y alto riesgo embólico no anticoagulado. Valorar inicio de anticoagulación oral."})
                categoria_riesgo = max(categoria_riesgo, "Muy alto", key=RANGO_RIESGO.get)
            elif puntos == 1:
                alertas.append({"tipo": "CARDIO", "nivel": "Moderado", "texto": "Valorar individualmente la indicación de anticoagulación (CHA2DS2-VA = 1)."})
        
        if ecg.get("fc_reposo", 0) >= 110:
            alertas.append({"tipo": "CARDIO", "nivel": "Moderado", "texto": "Descontrol de frecuencia de la FA. Revisar control de frecuencia."})

    if ecg.get("arritmia_ventricular_sostenida") or ecg.get("bloqueo_av_avanzado") or ecg.get("qt_largo"):
        alertas.append({"tipo": "CARDIO", "nivel": "Grave", "texto": "ALERTA MÉDICA URGENTE: Riesgo de muerte súbita. Derivación inmediata a cardiología."})
        categoria_riesgo = max(categoria_riesgo, "Muy alto", key=RANGO_RIESGO.get)
        
    # 7. OPORTUNIDADES PREVENTIVAS
    # Mantenemos "Albuminuria no registrada" para que la vista del Panel Semanal lo detecte bien
    if (diabetes or paciente_dict.get("hta")) and rac is None:
        alertas.append({"tipo": "RENAL", "nivel": "Moderado", "texto": "Albuminuria no registrada (Cribado KDIGO pendiente): Solicitar ratio albúmina/creatinina (RAC)."})

    return {
        "categoria": categoria_riesgo,
        "niveles": niveles,
        "alertas": alertas
    }

def clave_orden(resultado):
    cat_peso = {"Muy alto": 0, "Alto": 1, "Moderado": 2, "Bajo": 3}
    
    # Contamos los tipos de alertas
    num_graves = sum(1 for a in resultado["alertas"] if a["nivel"] == "Grave")
    num_moderadas = sum(1 for a in resultado["alertas"] if a["nivel"] == "Moderado")
    total_alertas = len(resultado["alertas"])
    
    # Ordenamos por: 1º Categoría, 2º Alertas Graves, 3º Alertas Moderadas, 4º Total Alertas
    return (
        cat_peso.get(resultado["categoria"], 4), 
        -num_graves, 
        -num_moderadas, 
        -total_alertas
    )