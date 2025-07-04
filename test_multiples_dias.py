"""
Script para probar automáticamente diferentes días de autonomía
y generar un reporte comparativo.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
from main import ejecutar_simulacion_completa, cargar_datos, calcular_energia_diaria
from scripts.calcular_banco_baterias import calcular_banco_baterias
from scripts.simular_soc import simular_soc_diario, analizar_resultados_soc


def simular_multiples_dias_autonomia_automatico():
    """
    Simula automáticamente el sistema para diferentes días de autonomía
    y genera un reporte comparativo.
    """
    
    print("🔄 SIMULACIÓN AUTOMÁTICA PARA MÚLTIPLES DÍAS DE AUTONOMÍA")
    print("="*70)
    
    # Días de autonomía a probar
    dias_autonomia_list = [1, 2, 3, 5, 7]
    
    # Almacenar resultados
    resultados_comparativos = []
    
    # Cargar datos una sola vez
    invierno, verano = cargar_datos()
    if invierno is None or verano is None:
        return
    
    energia_diaria = calcular_energia_diaria(invierno)
    
    # Parámetros del sistema
    PARAMETROS = {
        'voltaje_sistema': 48,
        'profundidad_descarga': 0.8,
        'voltaje_bateria': 12,
        'capacidad_bateria_ah': 200,
        'soc_inicial': 1.0,
        'soc_minimo': 0.2,
        'eficiencia_carga': 0.9,
        'eficiencia_descarga': 0.9
    }
    
    for dias in dias_autonomia_list:
        print(f"\n📅 Simulando para {dias} día(s) de autonomía...")
        
        # Calcular banco de baterías
        resultados_banco = calcular_banco_baterias(
            energia_diaria,
            dias,
            PARAMETROS['voltaje_sistema'],
            PARAMETROS['profundidad_descarga'],
            PARAMETROS['voltaje_bateria'],
            PARAMETROS['capacidad_bateria_ah']
        )
        
        capacidad_wh = resultados_banco["Capacidad Real [kWh]"] * 1000
        
        # Simular SOC
        soc_invierno = simular_soc_diario(
            invierno['Generacion_PV'],
            invierno['Consumo'],
            capacidad_wh,
            PARAMETROS['soc_inicial'],
            PARAMETROS['soc_minimo'],
            PARAMETROS['eficiencia_carga'],
            PARAMETROS['eficiencia_descarga']
        )
        
        soc_verano = simular_soc_diario(
            verano['Generacion_PV'],
            verano['Consumo'],
            capacidad_wh,
            PARAMETROS['soc_inicial'],
            PARAMETROS['soc_minimo'],
            PARAMETROS['eficiencia_carga'],
            PARAMETROS['eficiencia_descarga']
        )
        
        # Analizar resultados
        analisis_invierno = analizar_resultados_soc(soc_invierno)
        analisis_verano = analizar_resultados_soc(soc_verano)
        
        # Almacenar resultados
        resultado = {
            'Dias_Autonomia': dias,
            'Capacidad_Banco_kWh': resultados_banco["Capacidad Real [kWh]"],
            'Total_Baterias': resultados_banco["Total Baterías"],
            'SOC_Min_Invierno': analisis_invierno['SOC_Minimo'],
            'SOC_Min_Verano': analisis_verano['SOC_Minimo'],
            'SOC_Prom_Invierno': analisis_invierno['SOC_Promedio'],
            'SOC_Prom_Verano': analisis_verano['SOC_Promedio'],
            'Horas_Criticas_Invierno': analisis_invierno['Horas_Criticas'],
            'Horas_Criticas_Verano': analisis_verano['Horas_Criticas'],
            'Energia_Cargada_Invierno': analisis_invierno['Energia_Cargada_kWh'],
            'Energia_Cargada_Verano': analisis_verano['Energia_Cargada_kWh'],
            'Energia_Descargada_Invierno': analisis_invierno['Energia_Descargada_kWh'],
            'Energia_Descargada_Verano': analisis_verano['Energia_Descargada_kWh'],
            'Eficiencia_Invierno': analisis_invierno['Eficiencia_Sistema'],
            'Eficiencia_Verano': analisis_verano['Eficiencia_Sistema']
        }
        
        resultados_comparativos.append(resultado)
        
        print(f"  ✓ Completado: {dias} día(s) - {resultados_banco['Total Baterías']} baterías")
    
    # Crear DataFrame comparativo
    df_comparativo = pd.DataFrame(resultados_comparativos)
    
    # Guardar resultados
    df_comparativo.to_csv("results/comparacion_dias_autonomia.csv", index=False)
    
    # Generar gráficos comparativos
    generar_graficos_comparativos(df_comparativo)
    
    # Generar reporte
    generar_reporte_comparativo(df_comparativo)
    
    print(f"\n✅ Simulación automática completada!")
    print(f"📊 Resultados guardados en 'results/comparacion_dias_autonomia.csv'")
    print(f"📈 Gráficos comparativos generados en 'results/'")
    print(f"📋 Reporte generado en 'results/reporte_comparativo.txt'")


def generar_graficos_comparativos(df):
    """
    Genera gráficos comparativos para diferentes días de autonomía.
    """
    
    # Configurar estilo
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (15, 10)
    
    # Crear figura con subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    dias = df['Dias_Autonomia']
    
    # Gráfico 1: Capacidad del banco vs Días de autonomía
    ax1.plot(dias, df['Capacidad_Banco_kWh'], 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Días de Autonomía')
    ax1.set_ylabel('Capacidad del Banco (kWh)')
    ax1.set_title('Capacidad del Banco vs Días de Autonomía')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(dias)
    
    # Gráfico 2: SOC mínimo por estación
    ax2.plot(dias, df['SOC_Min_Invierno'], 'ro-', linewidth=2, markersize=8, label='Invierno')
    ax2.plot(dias, df['SOC_Min_Verano'], 'go-', linewidth=2, markersize=8, label='Verano')
    ax2.axhline(y=0.2, color='red', linestyle='--', alpha=0.7, label='SOC Mínimo (20%)')
    ax2.axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='SOC Crítico (30%)')
    ax2.set_xlabel('Días de Autonomía')
    ax2.set_ylabel('SOC Mínimo')
    ax2.set_title('SOC Mínimo vs Días de Autonomía')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(dias)
    ax2.set_ylim(0, 1)
    
    # Gráfico 3: Horas críticas
    ax3.plot(dias, df['Horas_Criticas_Invierno'], 'ro-', linewidth=2, markersize=8, label='Invierno')
    ax3.plot(dias, df['Horas_Criticas_Verano'], 'go-', linewidth=2, markersize=8, label='Verano')
    ax3.set_xlabel('Días de Autonomía')
    ax3.set_ylabel('Horas Críticas (SOC < 30%)')
    ax3.set_title('Horas Críticas vs Días de Autonomía')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xticks(dias)
    
    # Gráfico 4: Eficiencia del sistema
    ax4.plot(dias, df['Eficiencia_Invierno'], 'ro-', linewidth=2, markersize=8, label='Invierno')
    ax4.plot(dias, df['Eficiencia_Verano'], 'go-', linewidth=2, markersize=8, label='Verano')
    ax4.axhline(y=0.85, color='green', linestyle='--', alpha=0.7, label='Eficiencia Óptima (85%)')
    ax4.axhline(y=0.70, color='orange', linestyle='--', alpha=0.7, label='Eficiencia Mínima (70%)')
    ax4.set_xlabel('Días de Autonomía')
    ax4.set_ylabel('Eficiencia del Sistema')
    ax4.set_title('Eficiencia vs Días de Autonomía')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_xticks(dias)
    ax4.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig("results/comparacion_dias_autonomia.png", dpi=300, bbox_inches='tight')
    plt.show()
    
    print("  ✓ Gráfico comparativo guardado como 'results/comparacion_dias_autonomia.png'")


def generar_reporte_comparativo(df):
    """
    Genera un reporte de texto comparativo.
    """
    
    reporte = f"""
REPORTE COMPARATIVO - DÍAS DE AUTONOMÍA
{'='*60}

ENERGÍA DIARIA DEL SISTEMA: {df['Energia_Cargada_Invierno'].iloc[0] + df['Energia_Descargada_Invierno'].iloc[0]:.2f} kWh

RESUMEN POR DÍAS DE AUTONOMÍA:
{'='*60}

"""
    
    for _, row in df.iterrows():
        dias = row['Dias_Autonomia']
        capacidad = row['Capacidad_Banco_kWh']
        baterias = row['Total_Baterias']
        soc_min_inv = row['SOC_Min_Invierno']
        soc_min_ver = row['SOC_Min_Verano']
        horas_crit_inv = row['Horas_Criticas_Invierno']
        horas_crit_ver = row['Horas_Criticas_Verano']
        efic_inv = row['Eficiencia_Invierno']
        efic_ver = row['Eficiencia_Verano']
        
        # Evaluación del sistema
        if horas_crit_inv == 0 and horas_crit_ver == 0:
            evaluacion = "✅ EXCELENTE - Sin horas críticas"
        elif horas_crit_inv <= 2 and horas_crit_ver <= 2:
            evaluacion = "✅ BUENO - Pocas horas críticas"
        elif horas_crit_inv <= 6 and horas_crit_ver <= 6:
            evaluacion = "⚠️ ACEPTABLE - Algunas horas críticas"
        else:
            evaluacion = "❌ INSUFICIENTE - Muchas horas críticas"
        
        reporte += f"""
{dias} DÍA(S) DE AUTONOMÍA:
- Capacidad del banco: {capacidad:.2f} kWh
- Total de baterías: {baterias}
- SOC mínimo invierno: {soc_min_inv:.1%}
- SOC mínimo verano: {soc_min_ver:.1%}
- Horas críticas invierno: {horas_crit_inv}
- Horas críticas verano: {horas_crit_ver}
- Eficiencia invierno: {efic_inv:.1%}
- Eficiencia verano: {efic_ver:.1%}
- Evaluación: {evaluacion}
"""
    
    # Recomendación final
    reporte += f"""
{'='*60}
RECOMENDACIÓN FINAL:
{'='*60}

"""
    
    # Encontrar la mejor opción
    mejor_opcion = None
    for _, row in df.iterrows():
        if row['Horas_Criticas_Invierno'] == 0 and row['Horas_Criticas_Verano'] == 0:
            if mejor_opcion is None or row['Dias_Autonomia'] < mejor_opcion['Dias_Autonomia']:
                mejor_opcion = row
    
    if mejor_opcion is not None:
        reporte += f"""
✅ RECOMENDACIÓN ÓPTIMA: {mejor_opcion['Dias_Autonomia']} día(s) de autonomía
- Capacidad: {mejor_opcion['Capacidad_Banco_kWh']:.2f} kWh
- Baterías: {mejor_opcion['Total_Baterias']}
- Sin horas críticas en ninguna estación
- Eficiencia excelente
"""
    else:
        reporte += f"""
⚠️ RECOMENDACIÓN: Considerar aumentar la capacidad del sistema
- Ninguna configuración logra eliminar completamente las horas críticas
- Se recomienda al menos {df['Dias_Autonomia'].max() + 1} días de autonomía
"""
    
    # Guardar reporte
    with open("results/reporte_comparativo.txt", 'w', encoding='utf-8') as f:
        f.write(reporte)
    
    print(reporte)
    print("  ✓ Reporte guardado como 'results/reporte_comparativo.txt'")


if __name__ == "__main__":
    print("🚀 SIMULADOR COMPARATIVO - DÍAS DE AUTONOMÍA")
    print("="*70)
    
    # Crear directorio de resultados si no existe
    os.makedirs("results", exist_ok=True)
    
    # Ejecutar simulación automática
    simular_multiples_dias_autonomia_automatico() 