#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

def analizar_estacion(estacion, sheet_name, recurso_solar_file, cargas_file):
    """Analiza una estación específica (invierno o verano)"""
    
    print(f"\n{'='*80}")
    print(f"ANALIZANDO DATOS DE {estacion.upper()}")
    print(f"{'='*80}")
    
    # Archivos de salida específicos por estación
    output_png = f"/home/nicole/UA/OFFGRID/OFFGRID/results/sistema_fotovoltaico_{estacion.lower()}.png"
    output_csv = f"/home/nicole/UA/OFFGRID/OFFGRID/results/datos_sistema_fotovoltaico_{estacion.lower()}.csv"
    
    # 1. CARGAR DATOS DE IRRADIANCIA
    df_solar = pd.read_excel(recurso_solar_file, sheet_name=sheet_name)
    df_solar['Fecha_Hora'] = pd.to_datetime(df_solar['Fecha_Hora'])
    
    # 2. CARGAR Y PROCESAR DATOS DE CONSUMO
    df_cargas = pd.read_excel(cargas_file, header=0)
    carga_cols = [c for c in df_cargas.columns if c.lower() != "hora"]
    df_cargas["Hour"] = df_cargas["Hora"].astype(float)
    
    # Calcular consumo total por fila
    df_cargas["Total_Consumo"] = df_cargas[carga_cols].sum(axis=1)
    
    # Usar todos los valores originales con líneas normales
    df_hourly = df_cargas.set_index("Hour")[["Total_Consumo"]]
    
    print("🔍 VERIFICANDO DATOS DE CONSUMO:")
    print("Valores de consumo (primeros 10):")
    for hora, consumo in df_hourly["Total_Consumo"].head(10).items():
        print(f"   {hora:4.1f}h → {consumo:6.1f}W")
    
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
    # Graficar consumo con líneas normales
    ax2.plot(df_expandido['Hora'], df_expandido['Consumo'], color='red', linewidth=2)
    ax2.fill_between(df_expandido['Hora'], 0, df_expandido['Consumo'], alpha=0.3, color='red',
                     label=f'Consumo (Área = {np.trapz(df_expandido["Consumo"], df_expandido["Hora"])/1000:.2f} kWh)')
    ax2.set_ylabel('Consumo de energía (W)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.5)
    ax2.set_xlim(0, 24)
    
    # ============= PANEL 3: GENERACIÓN VS CONSUMO =============
    # Generación Fotovoltaica
    energia_pv_total = np.trapz(df_expandido['Generacion_PV'], df_expandido['Hora'])/1000
    ax3.plot(df_expandido['Hora'], df_expandido['Generacion_PV'], linewidth=2,
             label=f'Generación Fotovoltaica (Área = {energia_pv_total:.2f} kWh)', color='tab:purple')
    
    # Consumo con líneas normales
    energia_consumo_total = np.trapz(df_expandido['Consumo'], df_expandido['Hora'])/1000
    ax3.plot(df_expandido['Hora'], df_expandido['Consumo'], color='tab:red', linewidth=2,
             label=f'Consumo (Área = {energia_consumo_total:.2f} kWh)')
    
    # MÉTODO EXACTO DEL NOTEBOOK PROFESIONAL
    # Calcular diferencia energética (Generación - Consumo)
    diferencia_energia = df_expandido['Generacion_PV'] - df_expandido['Consumo']
    
    # Separar en positiva (exceso) y negativa (déficit)
    energia_disponible_positiva = diferencia_energia.clip(lower=0)
    energia_disponible_negativa = diferencia_energia.clip(upper=0)
    
    # Agregar los nuevos cálculos al DataFrame expandido
    df_expandido['Diferencia_Energia'] = diferencia_energia
    df_expandido['Exceso_Energia'] = energia_disponible_positiva  
    df_expandido['Deficit_Energia'] = energia_disponible_negativa
    
    # Graficar la línea de diferencia energética con líneas normales
    ax3.plot(df_expandido['Hora'], diferencia_energia,
             label='Energía Disponible', color='tab:orange', linewidth=2)
    
    # Calcular áreas
    energia_exceso_total = np.trapz(energia_disponible_positiva, df_expandido['Hora'])/1000
    energia_deficit_total = abs(np.trapz(energia_disponible_negativa, df_expandido['Hora'])/1000)
    
    # Rellenar áreas con líneas normales
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
    plt.suptitle(f'Sistema Fotovoltaico - {estacion.title()}', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.show()
    
    # 7. GENERAR CSV CON TODOS LOS DATOS GRAFICADOS
    print("=" * 70)
    print("GENERANDO ARCHIVO CSV CON DATOS GRAFICADOS...")
    print("=" * 70)
    
    # Crear DataFrame final con todos los datos para el CSV
    df_csv = df_expandido.copy()
    
    # Agregar columnas adicionales con información del sistema
    df_csv['Capacidad_Sistema_Wp'] = capacidad_max
    df_csv['Num_Modulos'] = num_modulos
    df_csv['Eficiencia_Modulo'] = eficiencia
    df_csv['Area_Total_m2'] = area_modulo * num_modulos
    df_csv['Perdidas_Sistema'] = perdidas
    
    # Calcular energías acumuladas hasta cada punto (integral numérica)
    df_csv['Energia_GHI_Acumulada_Wh'] = np.cumsum(df_csv['GHI_W_m2'] * 0.5)  # 0.5h por intervalo
    df_csv['Energia_Gmod_Acumulada_Wh'] = np.cumsum(df_csv['Gmod'] * 0.5)
    df_csv['Energia_PV_Acumulada_Wh'] = np.cumsum(df_csv['Generacion_PV'] * 0.5)
    df_csv['Energia_Consumo_Acumulada_Wh'] = np.cumsum(df_csv['Consumo'] * 0.5)
    
    # Reordenar columnas para mejor legibilidad
    columnas_ordenadas = [
        'Hora',
        'GHI_W_m2', 
        'Gmod',
        'Generacion_PV',
        'Consumo',
        'Diferencia_Energia',
        'Exceso_Energia', 
        'Deficit_Energia',
        'Energia_GHI_Acumulada_Wh',
        'Energia_Gmod_Acumulada_Wh', 
        'Energia_PV_Acumulada_Wh',
        'Energia_Consumo_Acumulada_Wh',
        'Capacidad_Sistema_Wp',
        'Num_Modulos',
        'Eficiencia_Modulo',
        'Area_Total_m2',
        'Perdidas_Sistema'
    ]
    
    df_csv = df_csv[columnas_ordenadas]
    
    # Guardar CSV
    df_csv.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"✅ Archivo CSV generado exitosamente: {output_csv}")
    print(f"📊 Datos incluidos: {len(df_csv)} filas x {len(df_csv.columns)} columnas") 
    print("📈 Columnas disponibles:")
    for i, col in enumerate(df_csv.columns, 1):
        print(f"   {i:2d}. {col}")
    
    # 8. IMPRIMIR RESUMEN
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
    
    return {
        'estacion': estacion,
        'energia_pv_total': energia_pv_total,
        'energia_consumo_total': energia_consumo_total,
        'energia_exceso_total': energia_exceso_total,
        'energia_deficit_total': energia_deficit_total,
        'balance_energetico': energia_pv_total - energia_consumo_total,
        'csv_file': output_csv,
        'png_file': output_png
    }

def main():
    """Función principal que analiza ambas estaciones"""
    
    # Rutas de archivos
    recurso_solar_file = "/home/nicole/UA/OFFGRID/OFFGRID/data/Recurso_solar.xlsx"
    cargas_file = "/home/nicole/UA/OFFGRID/OFFGRID/data/cargas_opt.xlsx"
    
    # Analizar ambas estaciones
    resultados = []
    
    # 1. INVIERNO
    resultado_invierno = analizar_estacion(
        estacion="Invierno",
        sheet_name="Solsticio_Invierno_20Jun", 
        recurso_solar_file=recurso_solar_file,
        cargas_file=cargas_file
    )
    resultados.append(resultado_invierno)
    
    # 2. VERANO  
    resultado_verano = analizar_estacion(
        estacion="Verano",
        sheet_name="Solsticio_Verano_21Dic",
        recurso_solar_file=recurso_solar_file, 
        cargas_file=cargas_file
    )
    resultados.append(resultado_verano)
    
    # 3. RESUMEN COMPARATIVO
    print(f"\n{'='*80}")
    print("RESUMEN COMPARATIVO ANUAL")
    print(f"{'='*80}")
    
    for resultado in resultados:
        print(f"\n🌟 {resultado['estacion'].upper()}:")
        print(f"   Generación PV: {resultado['energia_pv_total']:.2f} kWh/día")
        print(f"   Consumo:       {resultado['energia_consumo_total']:.2f} kWh/día") 
        print(f"   Balance:       {resultado['balance_energetico']:.2f} kWh/día")
        print(f"   Exceso:        {resultado['energia_exceso_total']:.2f} kWh/día")
        print(f"   Déficit:       {resultado['energia_deficit_total']:.2f} kWh/día")
    
    # Comparación
    diferencia_generacion = resultado_verano['energia_pv_total'] - resultado_invierno['energia_pv_total']
    print(f"\n📊 DIFERENCIA ESTACIONAL:")
    print(f"   Generación extra en verano: {diferencia_generacion:.2f} kWh/día ({diferencia_generacion/resultado_invierno['energia_pv_total']*100:.1f}% más)")
    
    print(f"\n📁 ARCHIVOS GENERADOS:")
    for resultado in resultados:
        print(f"   {resultado['estacion']}: {resultado['csv_file']}")
        print(f"   {resultado['estacion']}: {resultado['png_file']}")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()