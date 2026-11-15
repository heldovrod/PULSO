import json
from functools import lru_cache
from pathlib import Path
import pandas as pd
from core.risk_engine import evaluar

HOY = pd.Timestamp("2026-11-14")      # fecha fija
RUTA = Path(__file__).resolve().parent.parent / "data" / "patients.json"

@lru_cache
def cargar_pacientes():
    return json.loads(RUTA.read_text(encoding="utf-8"))

@lru_cache
def evaluar_cupo():
    return {p["id"]: evaluar(p, HOY) for p in cargar_pacientes()}