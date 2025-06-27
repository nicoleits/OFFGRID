#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

def main():
    # Rutas de archivos
    recurso_solar_file = "/home/nicole/UA/OFFGRID/OFFGRID/Recurso_solar.xlsx"
    cargas_file = "/home/nicole/UA/OFFGRID/OFFGRID/cargas.xlsx"
    output_png = "/home/nicole/UA/OFFGRID/OFFGRID/sistema_fotovoltaico_completo.png"
    
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
    
    # 5. EXPANDIR DATOS SOLARES PARA COINCIDIR CON RESOLUCIÓN DE CARGAS
    # En lugar de interpolar consumo, vamos a expandir los datos solares
    horas_expandidas = df_cargas['Hora'].values
    
    # Interpolar datos solares a resolución de medias horas
    ghi_expandido = np.interp(horas_expandidas, df_solar['Hora'], df_solar['GHI_W_m2'])
    gmod_expandido = np.interp(horas_expandidas, df_solar['Hora'], df_solar['Gmod'])
    
    # Crear DataFrame expandido
    df_expandido = pd.DataFrame({
        'Hora': horas_expandidas,
        'GHI_W_m2': ghi_expandido,
        'Gmod': gmod_expandido
    })
    
    # Calcular generación PV con resolución expandida
    df_expandido['Generacion_PV'] = (df_expandido['Gmod'] * area_modulo * eficiencia * num_modulos * (1 - perdidas))
    
    # Usar consumo original sin interpolar
    df_expandido['Consumo'] = df_hourly['Total_Consumo'].values
    
    # 6. CREAR EL GRÁFICO CON TRES PANELES
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # ============= PANEL 1: IRRADIANCIA SOLAR =============
    ax1.plot(df_expandido['Hora'], df_expandido['GHI_W_m2'], 'b-', linewidth=2, 
             label=f'GHI (Área = {np.trapz(df_expandido["GHI_W_m2"], df_expandido["Hora"])/1000:.2f} kWh/m²)', color='tab:blue')
    ax1.fill_between(df_expandido['Hora'], df_expandido['GHI_W_m2'], alpha=0.3, color='tab:blue')
    
    ax1.plot(df_expandido['Hora'], df_expandido['Gmod'], 'g-', linewidth=2,
             label=f'GHI Inclinado (Área = {np.trapz(df_expandido["Gmod"], df_expandido["Hora"])/1000:.2f} kWh/m²)', color='tab:green')
    ax1.fill_between(df_expandido['Hora'], df_expandido['Gmod'], alpha=0.3, color='tab:green')
    
    ax1.set_ylabel('GHI y GHI Inclinado (W/m²)', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.5)
    ax1.set_xlim(0, 24)
    
    # ============= PANEL 2: CONSUMO =============
    # Usar step para mostrar consumo como escalones rectangulares
    ax2.step(df_expandido['Hora'], df_expandido['Consumo'], where='pre', color='red', linewidth=2)
    ax2.fill_between(df_expandido['Hora'], 0, df_expandido['Consumo'], alpha=0.3, color='red',
                     step='pre', label=f'Consumo (Área = {np.trapz(df_expandido["Consumo"], df_expandido["Hora"])/1000:.2f} kWh)')
    ax2.set_ylabel('Consumo de energía (W)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.5)
    ax2.set_xlim(0, 24)
    
    # ============= PANEL 3: GENERACIÓN VS CONSUMO =============
    # Generación Fotovoltaica
    energia_pv_total = np.trapz(df_expandido['Generacion_PV'], df_expandido['Hora'])/1000
    ax3.plot(df_expandido['Hora'], df_expandido['Generacion_PV'], linewidth=2,
             label=f'Generación Fotovoltaica (Área = {energia_pv_total:.2f} kWh)', color='tab:purple')
    
    # Consumo con escalones rectangulares
    energia_consumo_total = np.trapz(df_expandido['Consumo'], df_expandido['Hora'])/1000
    ax3.step(df_expandido['Hora'], df_expandido['Consumo'], where='pre', color='tab:red', linewidth=2,
             label=f'Consumo (Área = {energia_consumo_total:.2f} kWh)')
    
    # MÉTODO EXACTO DEL NOTEBOOK PROFESIONAL
    # Calcular diferencia energética (Generación - Consumo)
    diferencia_energia = df_expandido['Generacion_PV'] - df_expandido['Consumo']
    
    # Graficar la línea de diferencia energética (como en el notebook)
    ax3.plot(df_expandido['Hora'], diferencia_energia, 
             label='Energía Disponible', color='tab:orange', linewidth=2)
    
    # Separar en positiva (exceso) y negativa (déficit)
    energia_disponible_positiva = diferencia_energia.clip(lower=0)
    energia_disponible_negativa = diferencia_energia.clip(upper=0)
    
    # Calcular áreas
    energia_exceso_total = np.trapz(energia_disponible_positiva, df_expandido['Hora'])/1000
    energia_deficit_total = abs(np.trapz(energia_disponible_negativa, df_expandido['Hora'])/1000)
    
    # SOLUCIÓN: Rellenar toda el área de diferencia con colores condicionales
    # Esto asegura que no haya gaps entre exceso y déficit
    ax3.fill_between(df_expandido['Hora'], 0, diferencia_energia, 
                     where=(diferencia_energia >= 0),
                     alpha=0.3, color='green', interpolate=True,
                     label=f'Exceso = {energia_exceso_total:.2f} kWh')
    
    ax3.fill_between(df_expandido['Hora'], 0, diferencia_energia, 
                     where=(diferencia_energia < 0),
                     alpha=0.3, color='red', interpolate=True,
                     label=f'Déficit = {energia_deficit_total:.2f} kWh')
    
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
    print(f"• Energía excedente: {energia_exceso_total:.2f} kWh/día")
    print(f"• Energía déficit: {energia_deficit_total:.2f} kWh/día")
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