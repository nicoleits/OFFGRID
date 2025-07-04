"""
Script integrado: recurso solar, demanda, generación FV y banco de baterías
"""
import pandas as pd
import numpy as np
from datetime import datetime
from OFFGRID.scripts.calcular_banco_baterias import calcular_banco_baterias, imprimir_resultados

# ================== PARÁMETROS EDITABLES ==================
# Archivos de entrada
RECURSO_SOLAR_FILE = "/home/nicole/UA/OFFGRID/OFFGRID/data/Recurso_solar.xlsx"
CARGAS_FILE = "/home/nicole/UA/OFFGRID/OFFGRID/data/cargas_opt.xlsx"
SHEET_NAME = "Solsticio_Invierno_20Jun"  # Cambia según el caso

# Parámetros del sistema FV
Pmax = 300  # Wp por módulo
eficiencia = 0.18
area_modulo = 1.6  # m²
capacidad_max = 3000  # Wp total
perdidas = 0.04

# Parámetros del banco de baterías
DIAS_AUTONOMIA = 1
VOLT_SISTEMA = 24
DOD = 0.8
VOLT_BATERIA = 12
CAP_BATERIA = 200  # Ah

# Archivo de salida resumen
OUTPUT_TXT = "OFFGRID/results/resumen_sistema_integrado.txt"

# ================== PROCESAMIENTO ==================
# 1. Cargar datos
print("Cargando datos de recurso solar y demanda...")
df_solar = pd.read_excel(RECURSO_SOLAR_FILE, sheet_name=SHEET_NAME)
df_solar['Fecha_Hora'] = pd.to_datetime(df_solar['Fecha_Hora'])
df_cargas = pd.read_excel(CARGAS_FILE, header=0)
carga_cols = [c for c in df_cargas.columns if c.lower() != "hora"]
df_cargas["Hour"] = df_cargas["Hora"].astype(float)
df_cargas["Total_Consumo"] = df_cargas[carga_cols].sum(axis=1)
df_hourly = df_cargas.set_index("Hour")[["Total_Consumo"]]

# 2. Calcular generación FV
num_modulos = capacidad_max / Pmax
# Expandir datos solares a resolución de carga
horas_expandidas = df_cargas['Hora'].values
gmod_expandido = np.interp(horas_expandidas, df_solar['Hora'], df_solar['Gmod'])
df_expandido = pd.DataFrame({
    'Hora': horas_expandidas,
    'Gmod': gmod_expandido
})
df_expandido['Generacion_PV'] = (df_expandido['Gmod'] * area_modulo * eficiencia * num_modulos * (1 - perdidas))
df_expandido['Consumo'] = df_hourly['Total_Consumo'].values

# 3. Cálculo de déficit diario
diferencia_energia = df_expandido['Generacion_PV'] - df_expandido['Consumo']
deficit = diferencia_energia.clip(upper=0)
deficit_diario_kwh = abs(np.trapz(deficit, df_expandido['Hora'])/1000)

# 4. Cálculo del banco de baterías
resultados_bateria = calcular_banco_baterias(
    energia_diaria_kwh=deficit_diario_kwh,
    dias_autonomia=DIAS_AUTONOMIA,
    voltaje_sistema=VOLT_SISTEMA,
    profundidad_descarga=DOD,
    voltaje_bateria=VOLT_BATERIA,
    capacidad_bateria_ah=CAP_BATERIA
)

# 5. Imprimir y guardar resumen
import sys
from io import StringIO

resumen = StringIO()
print("="*70, file=resumen)
print("RESUMEN DEL SISTEMA INTEGRADO", file=resumen)
print("="*70, file=resumen)
print(f"Consumo total diario: {np.trapz(df_expandido['Consumo'], df_expandido['Hora'])/1000:.2f} kWh", file=resumen)
print(f"Generación FV total diaria: {np.trapz(df_expandido['Generacion_PV'], df_expandido['Hora'])/1000:.2f} kWh", file=resumen)
print(f"Déficit diario (energía requerida para baterías): {deficit_diario_kwh:.2f} kWh", file=resumen)
print("-"*70, file=resumen)
imprimir_resultados(resultados_bateria)
print("="*70, file=resumen)

# Mostrar en consola
print(resumen.getvalue())
# Guardar en archivo
with open(OUTPUT_TXT, "w") as f:
    f.write(resumen.getvalue()) 