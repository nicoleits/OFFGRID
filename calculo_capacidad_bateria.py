
import pandas as pd

def estimar_capacidad_bateria(df, columna_diferencia='Diferencia_Energia',
                               dod=0.8, eficiencia=0.9):
    """
    Estima la capacidad necesaria del banco de baterías para cubrir déficit horario.

    Parámetros:
    - df: DataFrame con al menos una columna de diferencia energética (W).
    - columna_diferencia: nombre de la columna con el balance horario Pgen - Pcons (en W).
    - dod: profundidad máxima de descarga permitida (por ejemplo, 0.8 para litio).
    - eficiencia: eficiencia round-trip del sistema de almacenamiento.

    Retorna:
    - capacidad estimada (en kWh)
    """
    # Calcular déficit total (solo valores negativos)
    deficit_total_wh = df.loc[df[columna_diferencia] < 0, columna_diferencia].sum()
    deficit_total_kwh = abs(deficit_total_wh) / 1000  # convertir a kWh

    # Calcular capacidad total necesaria
    capacidad_total_kwh = deficit_total_kwh / (dod * eficiencia)

    return capacidad_total_kwh


df = pd.read_csv('/home/nicole/UA/NicoleTorres/OFFGRID/datos_sistema_fotovoltaico_invierno.csv')
capacidad_kwh = estimar_capacidad_bateria(df)
print(f"Capacidad estimada: {capacidad_kwh:.2f} kWh")
