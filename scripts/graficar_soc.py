"""
Script para generar gráficos de SOC, generación fotovoltaica y consumo.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Optional, Tuple


def configurar_estilo_graficos():
    """
    Configura el estilo de los gráficos para una mejor presentación.
    """
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3


def graficar_soc_diario(
    df: pd.DataFrame,
    titulo: str = "Simulación SOC Diario",
    guardar: bool = True,
    nombre_archivo: str = "soc_diario.png"
) -> None:
    """
    Genera un gráfico del SOC diario con generación y consumo.
    
    Args:
        df: DataFrame con datos de simulación
        titulo: Título del gráfico
        guardar: Si guardar el gráfico como archivo
        nombre_archivo: Nombre del archivo a guardar
    """
    
    configurar_estilo_graficos()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Gráfico superior: Generación y Consumo
    ax1.plot(df['Hora'], df['Generacion_PV'], 
             label='Generación FV', color='orange', linewidth=2, marker='o', markersize=4)
    ax1.plot(df['Hora'], df['Consumo'], 
             label='Consumo', color='red', linewidth=2, marker='s', markersize=4)
    ax1.fill_between(df['Hora'], df['Generacion_PV'], df['Consumo'], 
                     where=(df['Generacion_PV'] > df['Consumo']), 
                     alpha=0.3, color='green', label='Exceso')
    ax1.fill_between(df['Hora'], df['Generacion_PV'], df['Consumo'], 
                     where=(df['Generacion_PV'] < df['Consumo']), 
                     alpha=0.3, color='red', label='Déficit')
    
    ax1.set_ylabel('Potencia (W)')
    ax1.set_title(f'{titulo} - Generación y Consumo')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Gráfico inferior: SOC
    ax2.plot(df['Hora'], df['SOC'], 
             label='SOC', color='blue', linewidth=2, marker='o', markersize=4)
    ax2.axhline(y=0.2, color='red', linestyle='--', alpha=0.7, label='SOC Mínimo (20%)')
    ax2.axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='SOC Crítico (30%)')
    ax2.axhline(y=1.0, color='green', linestyle='--', alpha=0.7, label='SOC Máximo (100%)')
    
    ax2.set_ylabel('SOC (State of Charge)')
    ax2.set_xlabel('Hora del día')
    ax2.set_title('Estado de Carga de la Batería')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    if guardar:
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado como: {nombre_archivo}")
    
    plt.show()


def graficar_soc_multiple_dias(
    df: pd.DataFrame,
    titulo: str = "Simulación SOC Múltiples Días",
    guardar: bool = True,
    nombre_archivo: str = "soc_multiple_dias.png"
) -> None:
    """
    Genera un gráfico del SOC para múltiples días.
    
    Args:
        df: DataFrame con datos de simulación multi-día
        titulo: Título del gráfico
        guardar: Si guardar el gráfico como archivo
        nombre_archivo: Nombre del archivo a guardar
    """
    
    configurar_estilo_graficos()
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Crear eje X numérico para mejor visualización
    horas_numericas = range(len(df))
    
    # Gráfico de SOC
    ax.plot(horas_numericas, df['SOC'], 
            label='SOC', color='blue', linewidth=1.5, alpha=0.8)
    
    # Líneas de referencia
    ax.axhline(y=0.2, color='red', linestyle='--', alpha=0.7, label='SOC Mínimo (20%)')
    ax.axhline(y=0.3, color='orange', linestyle='--', alpha=0.7, label='SOC Crítico (30%)')
    ax.axhline(y=1.0, color='green', linestyle='--', alpha=0.7, label='SOC Máximo (100%)')
    
    # Marcar días
    horas_por_dia = 24
    for i in range(0, len(df), horas_por_dia):
        ax.axvline(x=i, color='gray', linestyle=':', alpha=0.5)
        if i < len(df):
            ax.text(i, 1.05, f'Día {i//horas_por_dia + 1}', 
                   rotation=45, ha='right', va='bottom', fontsize=8)
    
    ax.set_ylabel('SOC (State of Charge)')
    ax.set_xlabel('Horas')
    ax.set_title(titulo)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    if guardar:
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado como: {nombre_archivo}")
    
    plt.show()


def graficar_comparacion_estaciones(
    df_invierno: pd.DataFrame,
    df_verano: pd.DataFrame,
    guardar: bool = True,
    nombre_archivo: str = "comparacion_estaciones.png"
) -> None:
    """
    Genera un gráfico comparativo entre invierno y verano.
    
    Args:
        df_invierno: DataFrame con datos de invierno
        df_verano: DataFrame con datos de verano
        guardar: Si guardar el gráfico como archivo
        nombre_archivo: Nombre del archivo a guardar
    """
    
    configurar_estilo_graficos()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Gráfico superior: SOC comparativo
    ax1.plot(df_invierno['Hora'], df_invierno['SOC'], 
             label='Invierno', color='blue', linewidth=2, marker='o', markersize=4)
    ax1.plot(df_verano['Hora'], df_verano['SOC'], 
             label='Verano', color='orange', linewidth=2, marker='s', markersize=4)
    ax1.axhline(y=0.2, color='red', linestyle='--', alpha=0.7, label='SOC Mínimo (20%)')
    
    ax1.set_ylabel('SOC (State of Charge)')
    ax1.set_title('Comparación SOC - Invierno vs Verano')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1.1)
    
    # Gráfico inferior: Generación comparativa
    ax2.plot(df_invierno['Hora'], df_invierno['Generacion_PV'], 
             label='Generación Invierno', color='lightblue', linewidth=2, marker='o', markersize=4)
    ax2.plot(df_verano['Hora'], df_verano['Generacion_PV'], 
             label='Generación Verano', color='gold', linewidth=2, marker='s', markersize=4)
    ax2.plot(df_invierno['Hora'], df_invierno['Consumo'], 
             label='Consumo', color='red', linewidth=2, linestyle='--', alpha=0.7)
    
    ax2.set_ylabel('Potencia (W)')
    ax2.set_xlabel('Hora del día')
    ax2.set_title('Generación Fotovoltaica - Invierno vs Verano')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if guardar:
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado como: {nombre_archivo}")
    
    plt.show()


def graficar_balance_energetico(
    df: pd.DataFrame,
    titulo: str = "Balance Energético",
    guardar: bool = True,
    nombre_archivo: str = "balance_energetico.png"
) -> None:
    """
    Genera un gráfico del balance energético.
    
    Args:
        df: DataFrame con datos de simulación
        titulo: Título del gráfico
        guardar: Si guardar el gráfico como archivo
        nombre_archivo: Nombre del archivo a guardar
    """
    
    configurar_estilo_graficos()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Gráfico de balance energético
    ax.plot(df['Hora'], df['Balance_Energetico'], 
            label='Balance Energético', color='purple', linewidth=2, marker='o', markersize=4)
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    # Rellenar áreas
    ax.fill_between(df['Hora'], df['Balance_Energetico'], 0, 
                    where=(df['Balance_Energetico'] > 0), 
                    alpha=0.3, color='green', label='Exceso (Carga)')
    ax.fill_between(df['Hora'], df['Balance_Energetico'], 0, 
                    where=(df['Balance_Energetico'] < 0), 
                    alpha=0.3, color='red', label='Déficit (Descarga)')
    
    ax.set_ylabel('Balance Energético (W)')
    ax.set_xlabel('Hora del día')
    ax.set_title(titulo)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if guardar:
        plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado como: {nombre_archivo}")
    
    plt.show()


def crear_resumen_estadisticas(
    df_invierno: pd.DataFrame,
    df_verano: pd.DataFrame,
    guardar: bool = True,
    nombre_archivo: str = "resumen_estadisticas.txt"
) -> None:
    """
    Crea un archivo de texto con resumen de estadísticas.
    
    Args:
        df_invierno: DataFrame con datos de invierno
        df_verano: DataFrame con datos de verano
        guardar: Si guardar el resumen como archivo
        nombre_archivo: Nombre del archivo a guardar
    """
    
    # Calcular estadísticas
    stats_invierno = {
        'SOC_Minimo': df_invierno['SOC'].min(),
        'SOC_Maximo': df_invierno['SOC'].max(),
        'SOC_Promedio': df_invierno['SOC'].mean(),
        'Energia_Cargada_kWh': df_invierno['Energia_Cargada'].sum() / 1000,
        'Energia_Descargada_kWh': df_invierno['Energia_Descargada'].sum() / 1000,
        'Horas_Criticas': len(df_invierno[df_invierno['SOC'] < 0.3])
    }
    
    stats_verano = {
        'SOC_Minimo': df_verano['SOC'].min(),
        'SOC_Maximo': df_verano['SOC'].max(),
        'SOC_Promedio': df_verano['SOC'].mean(),
        'Energia_Cargada_kWh': df_verano['Energia_Cargada'].sum() / 1000,
        'Energia_Descargada_kWh': df_verano['Energia_Descargada'].sum() / 1000,
        'Horas_Criticas': len(df_verano[df_verano['SOC'] < 0.3])
    }
    
    # Crear texto del resumen
    resumen = f"""
RESUMEN DE ESTADÍSTICAS - SIMULACIÓN SOC
{'='*50}

INVIERNO:
- SOC Mínimo: {stats_invierno['SOC_Minimo']:.3f} ({stats_invierno['SOC_Minimo']*100:.1f}%)
- SOC Máximo: {stats_invierno['SOC_Maximo']:.3f} ({stats_invierno['SOC_Maximo']*100:.1f}%)
- SOC Promedio: {stats_invierno['SOC_Promedio']:.3f} ({stats_invierno['SOC_Promedio']*100:.1f}%)
- Energía Cargada: {stats_invierno['Energia_Cargada_kWh']:.2f} kWh
- Energía Descargada: {stats_invierno['Energia_Descargada_kWh']:.2f} kWh
- Horas Críticas (SOC < 30%): {stats_invierno['Horas_Criticas']}

VERANO:
- SOC Mínimo: {stats_verano['SOC_Minimo']:.3f} ({stats_verano['SOC_Minimo']*100:.1f}%)
- SOC Máximo: {stats_verano['SOC_Maximo']:.3f} ({stats_verano['SOC_Maximo']*100:.1f}%)
- SOC Promedio: {stats_verano['SOC_Promedio']:.3f} ({stats_verano['SOC_Promedio']*100:.1f}%)
- Energía Cargada: {stats_verano['Energia_Cargada_kWh']:.2f} kWh
- Energía Descargada: {stats_verano['Energia_Descargada_kWh']:.2f} kWh
- Horas Críticas (SOC < 30%): {stats_verano['Horas_Criticas']}

{'='*50}
"""
    
    print(resumen)
    
    if guardar:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(resumen)
        print(f"Resumen guardado como: {nombre_archivo}")


if __name__ == "__main__":
    print("Script de gráficos de SOC")
    print("Este script debe ser usado desde main.py") 