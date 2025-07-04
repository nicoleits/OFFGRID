#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

def main():
    # Rutas de archivos
    recurso_solar_file = "/home/nicole/UA//NicoleTorres/OFFGRID/Recurso_solar.xlsx"
    cargas_file = "/home/nicole/UA//NicoleTorres/OFFGRID/cargas_opt.xlsx"
    output_png = "/home/nicole/UA//NicoleTorres/OFFGRID/sistema_fotovoltaico_completo.png"
    
    # 1. CARGAR DATOS DE IRRADIANCIA
    df_solar = pd.read_excel(recurso_solar_file)
    df_solar['Fecha_Hora'] = pd.to_datetime(df_solar['Fecha_Hora'])
    
    # 2. CARGAR Y PROCESAR DATOS DE CONSUMO
    df_cargas = pd.read_excel(cargas_file, header=0)
    carga_cols = [c for c in df_cargas.columns if c.lower() != "hora"]
    df_cargas["Hour"] = df_cargas["Hora"].astype(float)
    
    # Agrupar por hora y sumar consumos
    df_hourly = df_cargas.groupby("Hour")[carga_cols].sum()
    df_hourly["Total_Consumo"] = df_hourly.sum(axis=1)
    
    # 3. PARÁMETROS DEL SISTEMA FOTOVOLTAICO
    Pmax = 300  # Wp por módulo
    eficiencia = 0.18  # Eficiencia del módulo
    area_modulo = 1.6  # m² por módulo
    capacidad_max = 3000  # Wp total del sistema
    num_modulos = capacidad_max / Pmax
    perdidas = 0.04  # 4% de pérdidas
    
    # 4. CALCULAR GENERACIÓN FOTOVOLTAICA
    # Usar Gmod (irradiancia en el plano del módulo)
    df_solar['Generacion_PV'] = (df_solar['Gmod'] * area_modulo * eficiencia * num_modulos * (1 - perdidas))
    
    # 5. INTERPOLAR CONSUMO PARA COINCIDIR CON HORAS SOLARES
    consumo_interpolado = np.interp(df_solar['Hora'], df_hourly.index, df_hourly['Total_Consumo'])
    df_solar['Consumo'] = consumo_interpolado
    
    # 6. CREAR EL GRÁFICO CON TRES PANELES
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # ============= PANEL 1: IRRADIANCIA SOLAR =============
    ax1.plot(df_solar['Hora'], df_solar['GHI_W_m2'], 'b-', linewidth=2, 
             label=f'GHI (Área = {np.trapz(df_solar["GHI_W_m2"], df_solar["Hora"])/1000:.2f} kWh/m²)', color='tab:blue')
    ax1.fill_between(df_solar['Hora'], df_solar['GHI_W_m2'], alpha=0.3, color='tab:blue')
    
    ax1.plot(df_solar['Hora'], df_solar['Gmod'], 'g-', linewidth=2,
             label=f'GHI Inclinado (Área = {np.trapz(df_solar["Gmod"], df_solar["Hora"])/1000:.2f} kWh/m²)', color='tab:green')
    ax1.fill_between(df_solar['Hora'], df_solar['Gmod'], alpha=0.3, color='tab:green')
    
    ax1.set_ylabel('GHI y GHI Inclinado (W/m²)', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.5)
    ax1.set_xlim(0, 24)
    
    # ============= PANEL 2: CONSUMO =============
    # Usar step para mostrar consumo como escalones rectangulares
    ax2.step(df_solar['Hora'], df_solar['Consumo'], where='pre', color='red', linewidth=2)
    ax2.fill_between(df_solar['Hora'], 0, df_solar['Consumo'], alpha=0.3, color='red',
                     step='pre', label=f'Consumo (Área = {np.trapz(df_solar["Consumo"], df_solar["Hora"])/1000:.2f} kWh)')
    ax2.set_ylabel('Consumo de energía (W)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.5)
    ax2.set_xlim(0, 24)
    
    # ============= PANEL 3: GENERACIÓN VS CONSUMO =============
    # Generación Fotovoltaica
    energia_pv_total = np.trapz(df_solar['Generacion_PV'], df_solar['Hora'])/1000
    ax3.plot(df_solar['Hora'], df_solar['Generacion_PV'], 'purple', linewidth=2,
             label=f'Generación Fotovoltaica (Área = {energia_pv_total:.2f} kWh)', color='tab:purple')
    
    # Consumo con escalones rectangulares
    energia_consumo_total = np.trapz(df_solar['Consumo'], df_solar['Hora'])/1000
    ax3.step(df_solar['Hora'], df_solar['Consumo'], where='pre', color='tab:red', linewidth=2,
             label=f'Consumo (Área = {energia_consumo_total:.2f} kWh)')
    
    # Exceso de energía (cuando generación > consumo)
    exceso = df_solar['Generacion_PV'] - df_solar['Consumo']
    exceso_positivo = np.where(exceso > 0, exceso, 0)
    
    # Área de exceso (verde)
    energia_exceso = np.trapz(exceso_positivo, df_solar['Hora'])/1000
    ax3.fill_between(df_solar['Hora'], df_solar['Consumo'], df_solar['Generacion_PV'], 
                     where=(df_solar['Generacion_PV'] >= df_solar['Consumo']), 
                     alpha=0.3, color='green', 
                     label=f'Energía Excedente = {energia_exceso:.2f} kWh')
    
    ax3.set_xlabel('Fecha', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Generación Fotovoltaica (W)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.5)
    ax3.set_xlim(0, 24)
    
    # Formatear eje x para mostrar horas
    hora_labels = [f"{int(h):02d}:00" for h in range(0, 25, 2)]
    hora_ticks = list(range(0, 25, 2))
    
    # Solo aplicar formato al último eje (ax3)
    ax3.set_xticks(hora_ticks)
    ax3.set_xticklabels(hora_labels, rotation=45)
    
    # Configuración general
    plt.xlabel('Fecha', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.show()
    
    # 7. IMPRIMIR RESUMEN
    print("=" * 70)
    print("RESUMEN DEL SISTEMA FOTOVOLTAICO")
    print("=" * 70)
    print("ESPECIFICACIONES DEL SISTEMA:")
    print(f"• Módulos: {num_modulos:.0f} x {Pmax}W")
    print(f"• Capacidad instalada: {capacidad_max:.0f} Wp ({capacidad_max/1000:.1f} kWp)")
    print(f"• Eficiencia del módulo: {eficiencia*100:.1f}%")
    print(f"• Área total de módulos: {area_modulo * num_modulos:.1f} m² ({area_modulo:.1f} m² cada uno)")
    print(f"• Pérdidas del sistema: {perdidas*100:.1f}%")
    print("-" * 70)
    print("RESULTADOS ENERGÉTICOS:")
    print(f"• Energía solar disponible (GHI): {np.trapz(df_solar['GHI_W_m2'], df_solar['Hora'])/1000:.2f} kWh/m²·día")
    print(f"• Energía solar inclinada (Gmod): {np.trapz(df_solar['Gmod'], df_solar['Hora'])/1000:.2f} kWh/m²·día")
    print(f"• Generación fotovoltaica total: {energia_pv_total:.2f} kWh/día")
    print(f"• Consumo total: {energia_consumo_total:.2f} kWh/día")
    print(f"• Energía excedente: {energia_exceso:.2f} kWh/día")
    print(f"• Balance energético: {energia_pv_total - energia_consumo_total:.2f} kWh/día")
    print("-" * 70)
    if energia_pv_total > energia_consumo_total:
        print("✅ SISTEMA SOBREDIMENSIONADO: La generación supera el consumo")
    elif energia_pv_total < energia_consumo_total:
        print("⚠️  SISTEMA SUBDIMENSIONADO: El consumo supera la generación")
    else:
        print("⚖️  SISTEMA BALANCEADO: Generación = Consumo")
    print("=" * 70)

if __name__ == "__main__":
    main()