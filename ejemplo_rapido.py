"""
Ejemplo rápido de uso del sistema fotovoltaico off-grid.
Este script demuestra las funcionalidades básicas del sistema.
"""

import sys
import os

# Agregar el directorio scripts al path
sys.path.append('scripts')

from scripts.calcular_banco_baterias import calcular_banco_baterias, imprimir_resultados
from scripts.simular_soc import simular_soc_diario, analizar_resultados_soc
from config import obtener_parametros_completos, imprimir_configuracion


def ejemplo_calculo_banco_baterias():
    """
    Ejemplo de cálculo del banco de baterías.
    """
    print("🔋 EJEMPLO: CÁLCULO DEL BANCO DE BATERÍAS")
    print("="*50)
    
    # Parámetros del ejemplo
    energia_diaria = 25.0  # kWh
    dias_autonomia = 2
    
    # Obtener parámetros del sistema
    parametros = obtener_parametros_completos(dias_autonomia)
    
    # Calcular banco de baterías
    resultados = calcular_banco_baterias(
        energia_diaria,
        dias_autonomia,
        parametros['voltaje_sistema'],
        parametros['profundidad_descarga'],
        parametros['voltaje_bateria'],
        parametros['capacidad_bateria_ah']
    )
    
    imprimir_resultados(resultados)
    
    return resultados


def ejemplo_simulacion_soc():
    """
    Ejemplo de simulación de SOC.
    """
    print("\n⚡ EJEMPLO: SIMULACIÓN DE SOC")
    print("="*50)
    
    # Datos de ejemplo (valores simplificados)
    import pandas as pd
    import numpy as np
    
    # Crear datos de ejemplo para 24 horas
    horas = list(range(24))
    generacion = [0] * 6 + [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1100, 1000, 900, 800, 700, 600, 500, 400, 300, 200, 100, 0]
    consumo = [300] * 24  # Consumo constante de 300W
    
    # Crear DataFrames
    df_ejemplo = pd.DataFrame({
        'Hora': horas,
        'Generacion_PV': generacion,
        'Consumo': consumo
    })
    
    # Parámetros de simulación
    parametros = obtener_parametros_completos(2)
    capacidad_wh = 50 * 1000  # 50 kWh en Wh
    
    print(f"Simulando SOC para un día con:")
    print(f"  - Capacidad del banco: {capacidad_wh/1000:.1f} kWh")
    print(f"  - SOC inicial: {parametros['soc_inicial']:.0%}")
    print(f"  - SOC mínimo: {parametros['soc_minimo']:.0%}")
    
    # Simular SOC
    resultados_soc = simular_soc_diario(
        df_ejemplo['Generacion_PV'],
        df_ejemplo['Consumo'],
        capacidad_wh,
        parametros['soc_inicial'],
        parametros['soc_minimo'],
        parametros['eficiencia_carga'],
        parametros['eficiencia_descarga']
    )
    
    # Analizar resultados
    analisis = analizar_resultados_soc(resultados_soc)
    
    print(f"\nResultados de la simulación:")
    print(f"  - SOC mínimo alcanzado: {analisis['SOC_Minimo']:.1%}")
    print(f"  - SOC promedio: {analisis['SOC_Promedio']:.1%}")
    print(f"  - Horas críticas: {analisis['Horas_Criticas']}")
    print(f"  - Energía cargada: {analisis['Energia_Cargada_kWh']:.2f} kWh")
    print(f"  - Energía descargada: {analisis['Energia_Descargada_kWh']:.2f} kWh")
    print(f"  - Eficiencia del sistema: {analisis['Eficiencia_Sistema']:.1%}")
    
    return resultados_soc


def ejemplo_comparacion_dias_autonomia():
    """
    Ejemplo de comparación entre diferentes días de autonomía.
    """
    print("\n📊 EJEMPLO: COMPARACIÓN DE DÍAS DE AUTONOMÍA")
    print("="*50)
    
    energia_diaria = 25.0  # kWh
    dias_a_comparar = [1, 2, 3]
    
    print(f"Comparando {len(dias_a_comparar)} configuraciones:")
    
    for dias in dias_a_comparar:
        parametros = obtener_parametros_completos(dias)
        
        # Calcular banco de baterías
        resultados = calcular_banco_baterias(
            energia_diaria,
            dias,
            parametros['voltaje_sistema'],
            parametros['profundidad_descarga'],
            parametros['voltaje_bateria'],
            parametros['capacidad_bateria_ah']
        )
        
        print(f"\n{dias} día(s) de autonomía:")
        print(f"  - Capacidad: {resultados['Capacidad Real [kWh]']:.1f} kWh")
        print(f"  - Baterías: {resultados['Total Baterías']}")
        print(f"  - Costo estimado: ${resultados['Total Baterías'] * 200}")  # $200 por batería
    
    print(f"\n💡 Recomendación: Para {energia_diaria:.1f} kWh/día,")
    print(f"   se recomiendan 2-3 días de autonomía para un balance")
    print(f"   óptimo entre confiabilidad y costo.")


def main():
    """
    Función principal del ejemplo.
    """
    print("🚀 EJEMPLO RÁPIDO - SISTEMA FOTOVOLTAICO OFF-GRID")
    print("="*60)
    
    # Mostrar configuración actual
    imprimir_configuracion()
    
    # Ejemplo 1: Cálculo de banco de baterías
    ejemplo_calculo_banco_baterias()
    
    # Ejemplo 2: Simulación de SOC
    ejemplo_simulacion_soc()
    
    # Ejemplo 3: Comparación de días de autonomía
    ejemplo_comparacion_dias_autonomia()
    
    print("\n" + "="*60)
    print("✅ EJEMPLO COMPLETADO")
    print("="*60)
    print("\nPara usar el sistema completo:")
    print("  python main.py                    # Simulación completa")
    print("  python test_multiples_dias.py     # Análisis comparativo")
    print("  python config.py                  # Ver configuración")
    
    print("\nPara personalizar el sistema:")
    print("  1. Edita config.py para cambiar parámetros")
    print("  2. Modifica main.py para ajustar la simulación")
    print("  3. Agrega tus propios datos en data/")
    
    print("\n📚 Documentación completa en README.md")


if __name__ == "__main__":
    main() 