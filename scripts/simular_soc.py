"""
Script para simular el estado de carga (SOC) de las baterías
para diferentes períodos y condiciones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


def simular_soc_diario(
    generacion_df: pd.DataFrame,
    demanda_df: pd.DataFrame,
    capacidad_almacenamiento_wh: float,
    soc_inicial: float = 1.0,
    soc_minimo: float = 0.2,
    eficiencia_carga: float = 0.9,
    eficiencia_descarga: float = 0.9
) -> pd.DataFrame:
    """
    Simula el SOC para un día completo.
    
    Args:
        generacion_df: DataFrame con datos de generación fotovoltaica
        demanda_df: DataFrame con datos de demanda/consumo
        capacidad_almacenamiento_wh: Capacidad del banco en Wh
        soc_inicial: SOC inicial (0.0 a 1.0)
        soc_minimo: SOC mínimo permitido (0.0 a 1.0)
        eficiencia_carga: Eficiencia de carga (0.0 a 1.0)
        eficiencia_descarga: Eficiencia de descarga (0.0 a 1.0)
    
    Returns:
        DataFrame con los resultados de la simulación
    """
    
    # Inicializar listas para almacenar resultados
    horas = []
    soc_list = []
    energia_bateria_list = []
    generacion_list = []
    consumo_list = []
    balance_energetico_list = []
    energia_cargada_list = []
    energia_descargada_list = []
    
    # Estado inicial
    energia_bateria = soc_inicial * capacidad_almacenamiento_wh
    energia_cargada_total = 0.0
    energia_descargada_total = 0.0
    
    # Simular cada hora
    for i in range(len(generacion_df)):
        hora = generacion_df.index[i] if hasattr(generacion_df.index[i], 'hour') else i
        generacion = generacion_df.iloc[i] if isinstance(generacion_df, pd.Series) else generacion_df.iloc[i, 0]
        consumo = demanda_df.iloc[i] if isinstance(demanda_df, pd.Series) else demanda_df.iloc[i, 0]
        
        # Balance energético
        balance = generacion - consumo
        
        # Calcular energía que entra/sale de la batería
        if balance > 0:  # Exceso de generación - cargar batería
            energia_cargada = balance * eficiencia_carga
            energia_bateria += energia_cargada
            energia_cargada_total += energia_cargada
            energia_descargada = 0.0
        else:  # Déficit - descargar batería
            energia_descargada = abs(balance) / eficiencia_descarga
            energia_bateria -= energia_descargada
            energia_descargada_total += energia_descargada
            energia_cargada = 0.0
        
        # Limitar la energía de la batería
        energia_bateria = max(soc_minimo * capacidad_almacenamiento_wh, 
                            min(capacidad_almacenamiento_wh, energia_bateria))
        
        # Calcular SOC
        soc = energia_bateria / capacidad_almacenamiento_wh
        
        # Almacenar resultados
        horas.append(hora)
        soc_list.append(soc)
        energia_bateria_list.append(energia_bateria)
        generacion_list.append(generacion)
        consumo_list.append(consumo)
        balance_energetico_list.append(balance)
        energia_cargada_list.append(energia_cargada)
        energia_descargada_list.append(energia_descargada)
    
    # Crear DataFrame de resultados
    resultados = pd.DataFrame({
        'Hora': horas,
        'Generacion_PV': generacion_list,
        'Consumo': consumo_list,
        'Balance_Energetico': balance_energetico_list,
        'Energia_Bateria_Wh': energia_bateria_list,
        'SOC': soc_list,
        'Energia_Cargada': energia_cargada_list,
        'Energia_Descargada': energia_descargada_list
    })
    
    # Agregar estadísticas
    resultados.attrs['energia_cargada_total_kwh'] = energia_cargada_total / 1000
    resultados.attrs['energia_descargada_total_kwh'] = energia_descargada_total / 1000
    resultados.attrs['soc_minimo_alcanzado'] = min(soc_list)
    resultados.attrs['soc_maximo_alcanzado'] = max(soc_list)
    
    return resultados


def simular_soc_multiple_dias(
    generacion_df: pd.DataFrame,
    demanda_df: pd.DataFrame,
    capacidad_almacenamiento_wh: float,
    num_dias: int = 7,
    soc_inicial: float = 1.0,
    soc_minimo: float = 0.2,
    eficiencia_carga: float = 0.9,
    eficiencia_descarga: float = 0.9
) -> pd.DataFrame:
    """
    Simula el SOC para múltiples días consecutivos.
    
    Args:
        generacion_df: DataFrame con datos de generación fotovoltaica (1 día)
        demanda_df: DataFrame con datos de demanda/consumo (1 día)
        capacidad_almacenamiento_wh: Capacidad del banco en Wh
        num_dias: Número de días a simular
        soc_inicial: SOC inicial (0.0 a 1.0)
        soc_minimo: SOC mínimo permitido (0.0 a 1.0)
        eficiencia_carga: Eficiencia de carga (0.0 a 1.0)
        eficiencia_descarga: Eficiencia de descarga (0.0 a 1.0)
    
    Returns:
        DataFrame con los resultados de la simulación multi-día
    """
    
    # Repetir los datos para múltiples días
    generacion_multi = pd.concat([generacion_df] * num_dias, ignore_index=True)
    demanda_multi = pd.concat([demanda_df] * num_dias, ignore_index=True)
    
    # Crear índice de tiempo para múltiples días
    horas_por_dia = len(generacion_df)
    tiempo_total = []
    for dia in range(num_dias):
        for hora in range(horas_por_dia):
            tiempo_total.append(f"Día {dia+1}, Hora {hora}")
    
    generacion_multi.index = tiempo_total
    demanda_multi.index = tiempo_total
    
    # Simular SOC
    resultados = simular_soc_diario(
        generacion_multi,
        demanda_multi,
        capacidad_almacenamiento_wh,
        soc_inicial,
        soc_minimo,
        eficiencia_carga,
        eficiencia_descarga
    )
    
    resultados.index = tiempo_total
    
    return resultados


def analizar_resultados_soc(df: pd.DataFrame) -> Dict:
    """
    Analiza los resultados de la simulación de SOC.
    
    Args:
        df: DataFrame con resultados de simulación
    
    Returns:
        Dict con estadísticas del análisis
    """
    
    # Estadísticas básicas
    soc_min = df['SOC'].min()
    soc_max = df['SOC'].max()
    soc_promedio = df['SOC'].mean()
    
    # Horas con SOC crítico (menor al 30%)
    horas_criticas = len(df[df['SOC'] < 0.3])
    
    # Energía total
    energia_cargada_total = df['Energia_Cargada'].sum() / 1000  # kWh
    energia_descargada_total = df['Energia_Descargada'].sum() / 1000  # kWh
    
    # Eficiencia del sistema
    eficiencia_sistema = (energia_descargada_total / energia_cargada_total) if energia_cargada_total > 0 else 0
    
    return {
        'SOC_Minimo': soc_min,
        'SOC_Maximo': soc_max,
        'SOC_Promedio': soc_promedio,
        'Horas_Criticas': horas_criticas,
        'Energia_Cargada_kWh': energia_cargada_total,
        'Energia_Descargada_kWh': energia_descargada_total,
        'Eficiencia_Sistema': eficiencia_sistema
    }


if __name__ == "__main__":
    # Ejemplo de uso
    print("Script de simulación de SOC")
    print("Este script debe ser usado desde main.py") 