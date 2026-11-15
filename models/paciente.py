from pydantic import BaseModel, Field
from typing import List, Optional, Union

class Antecedentes(BaseModel):
    infarto: bool = False
    ictus_ait: bool = False
    arteriopatia: bool = False
    insuficiencia_cardiaca: bool = False
    revascularizacion: bool = False

class ECG(BaseModel):
    ritmo: str = Field(..., description="Puede ser 'Normal', 'FA', 'extrasistoles'")
    arritmia_ventricular_sostenida: bool = False
    bloqueo_av_avanzado: bool = False
    qt_largo: bool = False
    anticoagulado: bool = False
    fc_reposo: int

class SeriesTemporales(BaseModel):
    egfr: List[List[Union[str, float]]] = []

class PacienteFHIR(BaseModel):
    id: str
    nombre: str
    edad: int
    sexo: str
    peso: Optional[float] = None    
    talla: Optional[float] = None   
    diabetes: bool
    hta: bool
    antecedentes: Antecedentes
    pa_tomas: List[List[int]] = [] 
    
    egfr: Optional[float] = None
    rac: Optional[float] = None
    ldl: Optional[float] = None
    hba1c: Optional[float] = None
    adherencia_baja: bool = False
    
    ecg: ECG
    medicacion: List[str] = []
    series: SeriesTemporales = SeriesTemporales()