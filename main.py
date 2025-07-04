"""
Script principal para ejecutar todo el flujo de cálculo y simulación
del sistema fotovoltaico off-grid con banco de baterías.
"""

import pandas as pd
import numpy as np
import sys
import os

# Agregar el directorio scripts al path
sys.path.append('scripts')

from scripts.calcular_banco_baterias import calcular_banco_baterias, imprimir_resultados
from scripts.simular_soc import simular_soc_diario, analizar_resultados_soc
from scripts.graficar_soc import (
    graficar_soc_diario, 
    graficar_comparacion_estaciones, 
    graficar_balance_energetico,
    crear_resumen_estadisticas
)


def cargar_datos():
    """
    Carga los datos de generación fotovoltaica y consumo.
    
    Returns:
        tuple: (datos_invierno, datos_verano)
    """
    try:
        # Cargar datos de generación fotovoltaica
        invierno = pd.read_csv("data/datos_sistema_fotovoltaico_invierno.csv")
        verano = pd.read_csv("data/datos_sistema_fotovoltaico_verano.csv")
        
        print("✓ Datos cargados exitosamente")
        print(f"  - Invierno: {len(invierno)} registros")
        print(f"  - Verano: {len(verano)} registros")
        
        return invierno, verano
        
    except FileNotFoundError as e:
        print(f"❌ Error: No se encontraron los archivos de datos")
        print(f"  Asegúrate de que los archivos estén en el directorio 'data/'")
        return None, None


def calcular_energia_diaria(df):
    """
    Calcula la energía diaria consumida a partir de los datos.
    
    Args:
        df: DataFrame con datos de consumo
    
    Returns:
        float: Energía diaria en kWh
    """
    # Asumiendo que la columna 'Consumo' está en W y los datos son horarios
    energia_diaria_wh = df['Consumo'].sum()
    energia_diaria_kwh = energia_diaria_wh / 1000
    return energia_diaria_kwh

def generar_tabla_energia_horaria(df, estacion):
    """
    Genera una tabla detallada con el total de energía por período de tiempo.
    
    Args:
        df: DataFrame con datos de consumo y generación
        estacion: String indicando la estación ('Invierno' o 'Verano')
    
    Returns:
        DataFrame: Tabla con energía por período
    """
    # Crear tabla de energía horaria
    tabla_energia = df.copy()
    
    # Determinar si los datos son de 30 minutos o 1 hora
    if len(df) == 48:  # 48 registros = 30 minutos
        periodo = "30 minutos"
        tabla_energia['Periodo'] = [f"{int(i//2):02d}:{int((i%2)*30):02d}" for i in range(48)]
    else:  # 24 registros = 1 hora
        periodo = "1 hora"
        tabla_energia['Periodo'] = [f"{i:02d}:00" for i in range(24)]
    
    # Calcular energía en kWh para cada período
    tabla_energia['Energia_Consumo_kWh'] = tabla_energia['Consumo'] / 1000  # Conversión W a kWh
    tabla_energia['Energia_Generacion_kWh'] = tabla_energia['Generacion_PV'] / 1000  # Conversión W a kWh
    
    # Calcular balance energético
    tabla_energia['Balance_Energia_kWh'] = tabla_energia['Energia_Generacion_kWh'] - tabla_energia['Energia_Consumo_kWh']
    
    # Calcular acumulados
    tabla_energia['Consumo_Acumulado_kWh'] = tabla_energia['Energia_Consumo_kWh'].cumsum()
    tabla_energia['Generacion_Acumulada_kWh'] = tabla_energia['Energia_Generacion_kWh'].cumsum()
    tabla_energia['Balance_Acumulado_kWh'] = tabla_energia['Balance_Energia_kWh'].cumsum()
    
    # Seleccionar columnas relevantes para la tabla final
    tabla_final = tabla_energia[[
        'Periodo', 
        'Consumo', 
        'Energia_Consumo_kWh',
        'Generacion_PV', 
        'Energia_Generacion_kWh',
        'Balance_Energia_kWh',
        'Consumo_Acumulado_kWh',
        'Generacion_Acumulada_kWh',
        'Balance_Acumulado_kWh'
    ]].copy()
    
    # Redondear valores para mejor presentación
    columnas_numericas = tabla_final.select_dtypes(include=[np.number]).columns
    tabla_final[columnas_numericas] = tabla_final[columnas_numericas].round(3)
    
    # Agregar información de la estación
    tabla_final['Estacion'] = estacion
    tabla_final['Periodo_Tiempo'] = periodo
    
    # Crear fila de totales
    fila_totales = pd.DataFrame({
        'Periodo': ['TOTAL'],
        'Consumo': [tabla_final['Consumo'].sum()],
        'Energia_Consumo_kWh': [tabla_final['Energia_Consumo_kWh'].sum()],
        'Generacion_PV': [tabla_final['Generacion_PV'].sum()],
        'Energia_Generacion_kWh': [tabla_final['Energia_Generacion_kWh'].sum()],
        'Balance_Energia_kWh': [tabla_final['Balance_Energia_kWh'].sum()],
        'Consumo_Acumulado_kWh': [tabla_final['Consumo_Acumulado_kWh'].iloc[-1]],
        'Generacion_Acumulada_kWh': [tabla_final['Generacion_Acumulada_kWh'].iloc[-1]],
        'Balance_Acumulado_kWh': [tabla_final['Balance_Acumulado_kWh'].iloc[-1]],
        'Estacion': [estacion],
        'Periodo_Tiempo': [periodo]
    })
    
    # Concatenar tabla original con fila de totales
    tabla_con_totales = pd.concat([tabla_final, fila_totales], ignore_index=True)
    
    return tabla_con_totales


def ejecutar_simulacion_completa(
    dias_autonomia: int = 2,
    voltaje_sistema: float = 48,
    profundidad_descarga: float = 0.8,
    voltaje_bateria: float = 12,
    capacidad_bateria_ah: float = 200,
    soc_inicial: float = 1.0,
    soc_minimo: float = 0.2,
    eficiencia_carga: float = 0.9,
    eficiencia_descarga: float = 0.9
):
    """
    Ejecuta la simulación completa del sistema.
    
    Args:
        dias_autonomia: Número de días de autonomía
        voltaje_sistema: Voltaje del sistema en V
        profundidad_descarga: Profundidad de descarga (0.0 a 1.0)
        voltaje_bateria: Voltaje nominal de cada batería en V
        capacidad_bateria_ah: Capacidad de cada batería en Ah
        soc_inicial: SOC inicial (0.0 a 1.0)
        soc_minimo: SOC mínimo permitido (0.0 a 1.0)
        eficiencia_carga: Eficiencia de carga (0.0 a 1.0)
        eficiencia_descarga: Eficiencia de descarga (0.0 a 1.0)
    """
    
    print("\n" + "="*60)
    print("SIMULACIÓN COMPLETA DEL SISTEMA FOTOVOLTAICO OFF-GRID")
    print("="*60)
    
    # 1. Cargar datos
    invierno, verano = cargar_datos()
    if invierno is None or verano is None:
        return
    
    # 2. Calcular energía diaria y generar tablas detalladas
    energia_diaria_invierno = calcular_energia_diaria(invierno)
    energia_diaria_verano = calcular_energia_diaria(verano)
    
    print(f"\n📊 ENERGÍA DIARIA CALCULADA:")
    print(f"  - Invierno: {energia_diaria_invierno:.2f} kWh")
    print(f"  - Verano: {energia_diaria_verano:.2f} kWh")
    
    # Generar tablas de energía horaria
    print(f"\n📋 GENERANDO TABLAS DE ENERGÍA HORARIA:")
    tabla_invierno = generar_tabla_energia_horaria(invierno, "Invierno")
    tabla_verano = generar_tabla_energia_horaria(verano, "Verano")
    
    # Guardar tablas en Excel
    with pd.ExcelWriter("results/tabla_energia_horaria.xlsx", engine='openpyxl') as writer:
        tabla_invierno.to_excel(writer, sheet_name='Energia_Invierno', index=False)
        tabla_verano.to_excel(writer, sheet_name='Energia_Verano', index=False)
        
        # Crear tabla comparativa
        tabla_comparativa = pd.concat([tabla_invierno, tabla_verano], ignore_index=True)
        tabla_comparativa.to_excel(writer, sheet_name='Comparacion_Estacional', index=False)
    
    print(f"  ✓ Tablas guardadas en 'results/tabla_energia_horaria.xlsx'")
    
    # Mostrar resumen de las tablas
    print(f"\n📈 RESUMEN DE ENERGÍA POR PERÍODO:")
    print(f"  - Período de tiempo: {tabla_invierno['Periodo_Tiempo'].iloc[0]}")
    print(f"  - Registros por día: {len(tabla_invierno)}")
    print(f"  - Consumo máximo invierno: {tabla_invierno['Consumo'].max()} W")
    print(f"  - Consumo máximo verano: {tabla_verano['Consumo'].max()} W")
    print(f"  - Generación máxima invierno: {tabla_invierno['Generacion_PV'].max():.1f} W")
    print(f"  - Generación máxima verano: {tabla_verano['Generacion_PV'].max():.1f} W")
    
    # Usar el valor más alto para el diseño
    energia_diaria_diseno = max(energia_diaria_invierno, energia_diaria_verano)
    
    # 3. Calcular banco de baterías
    print(f"\n🔋 CÁLCULO DEL BANCO DE BATERÍAS ({dias_autonomia} días de autonomía):")
    resultados_banco = calcular_banco_baterias(
        energia_diaria_diseno,
        dias_autonomia,
        voltaje_sistema,
        profundidad_descarga,
        voltaje_bateria,
        capacidad_bateria_ah
    )
    
    imprimir_resultados(resultados_banco)
    
    # 4. Simular SOC
    capacidad_wh = resultados_banco["Capacidad Real [kWh]"] * 1000
    
    print(f"\n⚡ SIMULACIÓN DE SOC:")
    print(f"  Capacidad del banco: {resultados_banco['Capacidad Real [kWh]']:.2f} kWh")
    
    # Simular para invierno
    print("\n  Simulando invierno...")
    soc_invierno = simular_soc_diario(
        invierno['Generacion_PV'],
        invierno['Consumo'],
        capacidad_wh,
        soc_inicial,
        soc_minimo,
        eficiencia_carga,
        eficiencia_descarga
    )
    
    # Simular para verano
    print("  Simulando verano...")
    soc_verano = simular_soc_diario(
        verano['Generacion_PV'],
        verano['Consumo'],
        capacidad_wh,
        soc_inicial,
        soc_minimo,
        eficiencia_carga,
        eficiencia_descarga
    )
    
    # 5. Analizar resultados
    print(f"\n📈 ANÁLISIS DE RESULTADOS:")
    
    analisis_invierno = analizar_resultados_soc(soc_invierno)
    analisis_verano = analizar_resultados_soc(soc_verano)
    
    print(f"\n  INVIERNO:")
    print(f"    - SOC mínimo: {analisis_invierno['SOC_Minimo']:.1%}")
    print(f"    - SOC promedio: {analisis_invierno['SOC_Promedio']:.1%}")
    print(f"    - Horas críticas: {analisis_invierno['Horas_Criticas']}")
    print(f"    - Energía cargada: {analisis_invierno['Energia_Cargada_kWh']:.2f} kWh")
    print(f"    - Energía descargada: {analisis_invierno['Energia_Descargada_kWh']:.2f} kWh")
    
    print(f"\n  VERANO:")
    print(f"    - SOC mínimo: {analisis_verano['SOC_Minimo']:.1%}")
    print(f"    - SOC promedio: {analisis_verano['SOC_Promedio']:.1%}")
    print(f"    - Horas críticas: {analisis_verano['Horas_Criticas']}")
    print(f"    - Energía cargada: {analisis_verano['Energia_Cargada_kWh']:.2f} kWh")
    print(f"    - Energía descargada: {analisis_verano['Energia_Descargada_kWh']:.2f} kWh")
    
    # 6. Generar gráficos
    print(f"\n📊 GENERANDO GRÁFICOS:")
    
    # Gráfico SOC diario invierno
    graficar_soc_diario(
        soc_invierno,
        "Simulación SOC - Invierno",
        True,
        "results/soc_invierno_diario.png"
    )
    
    # Gráfico SOC diario verano
    graficar_soc_diario(
        soc_verano,
        "Simulación SOC - Verano",
        True,
        "results/soc_verano_diario.png"
    )
    
    # Gráfico comparativo
    graficar_comparacion_estaciones(
        soc_invierno,
        soc_verano,
        True,
        "results/comparacion_estaciones.png"
    )
    
    # Gráfico balance energético invierno
    graficar_balance_energetico(
        soc_invierno,
        "Balance Energético - Invierno",
        True,
        "results/balance_energetico_invierno.png"
    )
    
    # Gráfico balance energético verano
    graficar_balance_energetico(
        soc_verano,
        "Balance Energético - Verano",
        True,
        "results/balance_energetico_verano.png"
    )
    
    # 7. Crear resumen
    crear_resumen_estadisticas(
        soc_invierno,
        soc_verano,
        True,
        "results/resumen_estadisticas.txt"
    )
    
    # 8. Guardar resultados en CSV
    print(f"\n💾 GUARDANDO RESULTADOS:")
    soc_invierno.to_csv("results/soc_invierno.csv", index=False)
    soc_verano.to_csv("results/soc_verano.csv", index=False)
    print("  ✓ Resultados guardados en directorio 'results/'")
    
    print(f"\n✅ SIMULACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)


def simular_multiples_dias_autonomia():
    """
    Simula el sistema para diferentes días de autonomía.
    """
    print("\n🔄 SIMULACIÓN PARA MÚLTIPLES DÍAS DE AUTONOMÍA")
    print("="*60)
    
    dias_autonomia_list = [1, 2, 3, 5]
    
    for dias in dias_autonomia_list:
        print(f"\n📅 Simulando para {dias} día(s) de autonomía:")
        ejecutar_simulacion_completa(dias_autonomia=dias)
        
        # Pausa entre simulaciones
        if dias != dias_autonomia_list[-1]:
            input("\nPresiona Enter para continuar con el siguiente escenario...")


if __name__ == "__main__":
    print("🚀 SISTEMA FOTOVOLTAICO OFF-GRID - SIMULADOR")
    print("="*60)
    
    # Crear directorio de resultados si no existe
    os.makedirs("results", exist_ok=True)
    
    # Parámetros por defecto
    PARAMETROS_DEFAULT = {
        'dias_autonomia': 2,
        'voltaje_sistema': 48,
        'profundidad_descarga': 0.8,
        'voltaje_bateria': 12,
        'capacidad_bateria_ah': 200,
        'soc_inicial': 1.0,
        'soc_minimo': 0.2,
        'eficiencia_carga': 0.9,
        'eficiencia_descarga': 0.9
    }
    
    print("Parámetros por defecto:")
    for param, valor in PARAMETROS_DEFAULT.items():
        print(f"  - {param}: {valor}")
    
    # Ejecutar simulación principal
    ejecutar_simulacion_completa(**PARAMETROS_DEFAULT)
    
    # Preguntar si quiere simular múltiples días de autonomía
    print(f"\n" + "="*60)
    respuesta = input("¿Deseas simular para múltiples días de autonomía? (s/n): ").lower()
    
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        simular_multiples_dias_autonomia()
    
    print(f"\n🎉 ¡Simulación completada! Revisa los resultados en el directorio 'results/'") 