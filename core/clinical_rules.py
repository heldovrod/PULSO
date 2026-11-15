NIVELES = ["Normal", "Leve", "Moderado", "Grave"]


def nivel_max(*ns):
    return max(ns, key=NIVELES.index)


def ge(x, lim): return x is not None and x >= lim
def lt(x, lim): return x is not None and x < lim


# ---------- 1.1 Presión arterial ----------
def pa_media(tomas):                  
    n = len(tomas)
    return sum(t[0] for t in tomas) / n, sum(t[1] for t in tomas) / n


def clasificar_pa(sis, dia):        
    # Nomenclatura y cortes oficiales del documento (ESH 2023)
    if sis >= 180 or dia >= 110: return "HTA grado III"
    if sis >= 160 or dia >= 100: return "HTA grado II"
    if sis >= 140 or dia >= 90: return "HTA grado I"
    if sis >= 130 or dia >= 85: return "Normal-alta"
    if sis >= 120 or dia >= 80: return "Normal"
    return "Óptima"


NIVEL_PA = {
    "Óptima": "Normal", 
    "Normal": "Normal", 
    "Normal-alta": "Leve",
    "HTA grado I": "Leve", 
    "HTA grado II": "Moderado",
    "HTA grado III": "Grave"
}   


# ---------- 1.3 Lípidos ----------
def nivel_por_cortes(valor, cortes): 
    for limite, nivel in cortes:
        if valor < limite:
            return nivel
    return "Grave"


CORTES_TG = [(150, "Normal"), (200, "Leve"), (500, "Moderado")]
CORTES_LPA = [(75, "Normal"), (125, "Leve"), (430, "Moderado")]   

# Mismas claves que usa el motor clínico (Bajo, Moderado, Alto, Muy alto)
OBJETIVO_LDL = {
    "Muy alto": 55, 
    "Alto": 70, 
    "Moderado": 100, 
    "Bajo": 116
}   


def nivel_por_exceso(exceso):        
    if exceso <= 0: return "Normal"
    if exceso < 20: return "Leve"
    if exceso < 50: return "Moderado"
    return "Grave"