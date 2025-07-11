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
    print(f"\n🔍 DIAGNÓSTICO DE DATOS SOLARES")
    print("=" * 50)
    
    df_solar = pd.read_excel(recurso_solar_file, sheet_name=sheet_name)
    print(f"📁 Archivo solar: {recurso_solar_file}")
    print(f"📋 Hoja: {sheet_name}")
    print(f"✅ Datos solares cargados: {len(df_solar)} filas x {len(df_solar.columns)} columnas")
    
    # Mostrar estructura de datos solares
    print(f"\n📊 ESTRUCTURA DE DATOS SOLARES:")
    print(f"   Columnas disponibles: {list(df_solar.columns)}")
    print(f"   Tipos de datos:")
    for col in df_solar.columns:
        print(f"     {col}: {df_solar[col].dtype}")
    
    # Mostrar primeros registros solares
    print(f"\n📋 PRIMEROS 5 REGISTROS SOLARES:")
    print(df_solar.head())
    
    # Verificar datos faltantes en solar
    print(f"\n❓ DATOS FALTANTES EN SOLAR:")
    for col in df_solar.columns:
        faltantes = df_solar[col].isnull().sum()
        if faltantes > 0:
            print(f"   {col}: {faltantes} valores faltantes")
        else:
            print(f"   {col}: Sin datos faltantes")
    
    df_solar['Fecha_Hora'] = pd.to_datetime(df_solar['Fecha_Hora'])
    
    print(f"\n📈 ESTADÍSTICAS SOLARES:")
    print(f"   GHI máximo: {df_solar['GHI_W_m2'].max():.1f} W/m²")
    print(f"   GHI mínimo: {df_solar['GHI_W_m2'].min():.1f} W/m²")
    print(f"   GHI promedio: {df_solar['GHI_W_m2'].mean():.1f} W/m²")
    print(f"   Gmod máximo: {df_solar['Gmod'].max():.1f} W/m²")
    print(f"   Gmod mínimo: {df_solar['Gmod'].min():.1f} W/m²")
    print(f"   Gmod promedio: {df_solar['Gmod'].mean():.1f} W/m²")
    print(f"   Horas disponibles: {sorted(df_solar['Hora'].unique())}")
    
    # 2. CARGAR Y PROCESAR DATOS DE CONSUMO
    print(f"\n🔍 DIAGNÓSTICO DE DATOS DE CONSUMO")
    print("=" * 50)
    
    df_cargas = pd.read_excel(cargas_file, header=0)
    print(f"📁 Archivo de cargas: {cargas_file}")
    print(f"✅ Datos cargados: {len(df_cargas)} filas x {len(df_cargas.columns)} columnas")
    
    # Mostrar estructura de datos de consumo
    print(f"\n📊 ESTRUCTURA DE DATOS DE CONSUMO:")
    print(f"   Columnas disponibles: {list(df_cargas.columns)}")
    print(f"   Tipos de datos:")
    for col in df_cargas.columns:
        print(f"     {col}: {df_cargas[col].dtype}")
    
    # Mostrar primeros registros
    print(f"\n📋 PRIMEROS 5 REGISTROS DE CONSUMO:")
    print(df_cargas.head())
    
    # Verificar datos faltantes en consumo
    print(f"\n❓ DATOS FALTANTES EN CONSUMO:")
    for col in df_cargas.columns:
        faltantes = df_cargas[col].isnull().sum()
        if faltantes > 0:
            print(f"   {col}: {faltantes} valores faltantes")
        else:
            print(f"   {col}: Sin datos faltantes")
    
    carga_cols = [c for c in df_cargas.columns if c.lower() != "hora"]
    print(f"\n🔧 PROCESANDO DATOS DE CONSUMO:")
    print(f"   Columnas de carga identificadas: {carga_cols}")
    print(f"   Total de columnas de carga: {len(carga_cols)}")
    
    # Convertir hora
    df_cargas["Hour"] = df_cargas["Hora"].astype(float)
    print(f"   Horas únicas en datos: {sorted(df_cargas['Hour'].unique())}")
    
    # Calcular consumo total por fila
    df_cargas["Total_Consumo"] = df_cargas[carga_cols].sum(axis=1)
    print(f"\n📊 CONSUMO TOTAL POR FILA:")
    print(f"   Consumo máximo por fila: {df_cargas['Total_Consumo'].max():.1f} W")
    print(f"   Consumo mínimo por fila: {df_cargas['Total_Consumo'].min():.1f} W")
    print(f"   Consumo promedio por fila: {df_cargas['Total_Consumo'].mean():.1f} W")
    
    # Mostrar algunos ejemplos de consumo
    print(f"\n📋 EJEMPLOS DE CONSUMO POR FILA:")
    for i in range(min(5, len(df_cargas))):
        fila = df_cargas.iloc[i]
        print(f"   Fila {i+1}: Hora={fila['Hour']:.1f}, Total={fila['Total_Consumo']:.1f}W")
        for col in carga_cols:
            if fila[col] > 0:
                print(f"     {col}: {fila[col]:.1f}W")
    
    # Usar todos los valores originales con líneas normales
    df_hourly = df_cargas.set_index("Hour")[["Total_Consumo"]]
    print(f"\n📈 DATOS AGRUPADOS POR HORA:")
    print(f"   Filas resultantes: {len(df_hourly)}")
    print(f"   Horas disponibles: {sorted(df_hourly.index)}")
    
    print(f"\n🔍 VERIFICANDO DATOS DE CONSUMO:")
    print("Valores de consumo (primeros 10):")
    for hora, consumo in df_hourly["Total_Consumo"].head(10).items():
        print(f"   {hora:4.1f}h → {consumo:6.1f}W")
    
    # 3. PARÁMETROS DEL SISTEMA FOTOVOLTAICO
    Pmax = 580  # Wp por módulo
    eficiencia = 0.221  # Eficiencia del módulo
    area_modulo = 2.645  # m² por módulo
    capacidad_max = 17400  # Wp total del sistema
    num_modulos = capacidad_max / Pmax
    perdidas = 0.04  # 4% de pérdidas
    
    PR = 0.8
    ef_inv = 0.976

    # 4. CALCULAR GENERACIÓN FOTOVOLTAICA
    # Usar Gmod (irradiancia en el plano del módulo)
    df_solar['Generacion_PV'] = (df_solar['Gmod'] * area_modulo * eficiencia * num_modulos * PR * ef_inv) #(1 - perdidas))
    # ▸ Comprobación paso a paso
    print("=== CHECK INTERMEDIO ===")
    print(f"Hβ integrada ............... {df_solar['Gmod'].sum()/1000:.2f} kWh/m²")
    print(f"Área total módulos ......... {area_modulo*num_modulos:.2f} m²")
    print(f"η módulo ................... {eficiencia:.3f}")
    print(f"PR campo (sin inversor) .... {PR:.3f}")
    print(f"η inversor ................. {ef_inv:.3f}")
    print(f"Factor total (excepto área)  {(eficiencia*PR*ef_inv):.3f}")
    print(f"Energía AC diaria calculada  {df_solar['Generacion_PV'].sum()/1000:.2f} kWh")
    print("==========================")
    
    H_inv_real = np.trapz(df_solar['Gmod'], df_solar['Hora']) / 1000  # kWh/m²
    print(f"🔎 Gmod integrado (hoja Excel) = {H_inv_real:.2f} kWh/m² día")

    # 5. EXPANDIR DATOS SOLARES PARA COINCIDIR CON RESOLUCIÓN DE CARGAS
    print(f"\n🔍 DIAGNÓSTICO DE RESOLUCIÓN TEMPORAL:")
    print("=" * 50)
    print(f"   Datos solares: {len(df_solar)} filas (resolución horaria)")
    print(f"   Datos consumo: {len(df_cargas)} filas (resolución media hora)")
    print(f"   Horas solares: {sorted(df_solar['Hora'].unique())}")
    print(f"   Horas consumo: {sorted(df_cargas['Hora'].unique())[:10]}...")  # Mostrar solo las primeras 10
    
    # Verificar si necesitamos interpolar
    if len(df_solar) != len(df_cargas):
        print(f"⚠️  ADVERTENCIA: Resoluciones temporales diferentes")
        print(f"   Interpolando datos solares de {len(df_solar)} a {len(df_cargas)} puntos")
    else:
        print(f"✅ Resoluciones temporales coinciden")
    
    # En lugar de interpolar consumo, vamos a expandir los datos solares
    horas_expandidas = df_cargas['Hora'].values
    
    # Interpolar datos solares a resolución de medias horas
    ghi_expandido = np.interp(horas_expandidas, df_solar['Hora'], df_solar['GHI_W_m2'])
    gmod_expandido = np.interp(horas_expandidas, df_solar['Hora'], df_solar['Gmod'])
    
    print(f"   Datos interpolados: {len(ghi_expandido)} puntos")
    print(f"   GHI interpolado - Max: {ghi_expandido.max():.1f}, Min: {ghi_expandido.min():.1f}")
    print(f"   Gmod interpolado - Max: {gmod_expandido.max():.1f}, Min: {gmod_expandido.min():.1f}")
    
    # Crear DataFrame expandido
    df_expandido = pd.DataFrame({
        'Hora': horas_expandidas,
        'GHI_W_m2': ghi_expandido,
        'Gmod': gmod_expandido
    })
    
    # Calcular generación PV con resolución expandida
    df_expandido['Generacion_PV'] = (df_expandido['Gmod'] * area_modulo * eficiencia * num_modulos * PR * ef_inv) #(1 - perdidas))
    
    # Usar consumo original sin interpolar
    df_expandido['Consumo'] = df_hourly['Total_Consumo'].values
    
    print(f"\n🔍 VERIFICACIÓN FINAL DE CONSUMO:")
    print(f"   Longitud de datos expandidos: {len(df_expandido)}")
    print(f"   Longitud de datos de consumo: {len(df_hourly)}")
    print(f"   Consumo máximo en datos expandidos: {df_expandido['Consumo'].max():.1f} W")
    print(f"   Consumo mínimo en datos expandidos: {df_expandido['Consumo'].min():.1f} W")
    print(f"   Consumo promedio en datos expandidos: {df_expandido['Consumo'].mean():.1f} W")
    
    # CORREGIR: Calcular consumo total diario correctamente
    # Los datos están en resolución de media hora, pero representan el consumo promedio por intervalo
    # Para obtener el consumo diario: sumar todos y dividir por 24 para obtener W/hora promedio
    consumo_promedio_por_hora = df_expandido['Consumo'].sum() / 24  # W/hora promedio
    consumo_total_wh = consumo_promedio_por_hora * 24  # W/hora * 24 horas = Wh/día
    energia_consumo_total = consumo_promedio_por_hora * 24 / 1000  # W/hora * 24h / 1000 = kWh/día
    print(f"   Consumo promedio por hora: {consumo_promedio_por_hora:.1f} W/hora")
    print(f"   Consumo total diario (CORREGIDO): {consumo_total_wh:.1f} Wh")
    print(f"   Consumo total diario (kWh): {consumo_total_wh/1000:.3f} kWh")
    
    # Verificar que los datos coincidan
    if len(df_expandido) != len(df_hourly):
        print(f"⚠️  ADVERTENCIA: Longitudes diferentes - Expandido: {len(df_expandido)}, Hourly: {len(df_hourly)}")
    else:
        print(f"✅ Longitudes coinciden: {len(df_expandido)}")
    
    # 6. CREAR EL GRÁFICO CON TRES PANELES
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    
    # ============= PANEL 1: IRRADIANCIA SOLAR =============
    # Convertir a kW/m²
    ghi_kw = df_expandido['GHI_W_m2'] / 1000
    gmod_kw = df_expandido['Gmod'] / 1000
    
    # Calcular energías usando método coherente
    energia_ghi_total = np.sum(ghi_kw) * 0.5  # kW/m² * 0.5h = kWh/m²
    energia_gmod_total = np.sum(gmod_kw) * 0.5  # kW/m² * 0.5h = kWh/m²
    
    ax1.plot(df_expandido['Hora'], ghi_kw, 'b-', linewidth=2, 
             label=f'GHI (Total = {energia_ghi_total:.3f} kWh/m²)', color='tab:blue')
    ax1.fill_between(df_expandido['Hora'], ghi_kw, alpha=0.3, color='tab:blue')
    
    ax1.plot(df_expandido['Hora'], gmod_kw, 'g-', linewidth=2,
             label=f'Gmod (Total = {energia_gmod_total:.3f} kWh/m²)', color='tab:green')
    ax1.fill_between(df_expandido['Hora'], gmod_kw, alpha=0.3, color='tab:green')
    
    ax1.set_ylabel('GHI y Gmod (kW/m²)', fontsize=16, fontweight='bold')
    ax1.legend(fontsize=14)
    ax1.grid(True, alpha=0.5)
    ax1.set_xlim(0, 24)
    
    # ============= PANEL 2: CONSUMO =============
    # Convertir consumo a kW
    consumo_kw = df_expandido['Consumo'] / 1000
    
    # Graficar consumo con líneas normales
    ax2.plot(df_expandido['Hora'], consumo_kw, color='red', linewidth=2)
    ax2.fill_between(df_expandido['Hora'], 0, consumo_kw, alpha=0.3, color='red',
                     label=f'Consumo (Total = {energia_consumo_total:.3f} kWh)')
    ax2.set_ylabel('Consumo (kW)', fontsize=16, fontweight='bold')
    ax2.legend(fontsize=14)
    ax2.grid(True, alpha=0.5)
    ax2.set_xlim(0, 24)
    
    # ============= PANEL 3: GENERACIÓN VS CONSUMO =============
    # Convertir generación PV a kW
    generacion_pv_kw = df_expandido['Generacion_PV'] / 1000
    
    # Generación Fotovoltaica
    # Usar método coherente: sumatoria con factor de 0.5h por intervalo
    energia_pv_total = np.sum(generacion_pv_kw) * 0.5  # kW * 0.5h = kWh
    ax3.plot(df_expandido['Hora'], generacion_pv_kw, linewidth=2,
             label=f'Generación PV (Total = {energia_pv_total:.3f} kWh)', color='tab:purple')
    
    # Consumo con líneas normales
    ax3.plot(df_expandido['Hora'], consumo_kw, color='tab:red', linewidth=2,
             label=f'Consumo (Total = {energia_consumo_total:.3f} kWh)')
    
    # MÉTODO EXACTO DEL NOTEBOOK PROFESIONAL
    # Calcular diferencia energética (Generación - Consumo) en kW
    diferencia_energia_kw = generacion_pv_kw - consumo_kw
    
    # Separar en positiva (exceso) y negativa (déficit)
    energia_disponible_positiva = diferencia_energia_kw.clip(lower=0)
    energia_disponible_negativa = diferencia_energia_kw.clip(upper=0)
    
    # Agregar los nuevos cálculos al DataFrame expandido
    df_expandido['Diferencia_Energia_kW'] = diferencia_energia_kw
    df_expandido['Exceso_Energia_kW'] = energia_disponible_positiva  
    df_expandido['Deficit_Energia_kW'] = energia_disponible_negativa
    
    # Graficar la línea de diferencia energética con líneas normales
    ax3.plot(df_expandido['Hora'], diferencia_energia_kw,
             label='Energía Disponible', color='tab:orange', linewidth=2)
    
    # Calcular áreas usando método coherente
    # Usar sumatoria con factor de 0.5h por intervalo para ser coherente con el cálculo de consumo
    energia_exceso_total = np.sum(energia_disponible_positiva) * 0.5  # kW * 0.5h = kWh
    energia_deficit_total = abs(np.sum(energia_disponible_negativa)) * 0.5  # kW * 0.5h = kWh
    
    # Rellenar áreas con líneas normales
    ax3.fill_between(df_expandido['Hora'], 0, diferencia_energia_kw, 
                     where=(diferencia_energia_kw >= 0),
                     alpha=0.3, color='green', interpolate=True,
                     label=f'Exceso = {energia_exceso_total:.3f} kWh')
    
    ax3.fill_between(df_expandido['Hora'], 0, diferencia_energia_kw, 
                     where=(diferencia_energia_kw < 0),
                     alpha=0.3, color='red', interpolate=True,
                     label=f'Déficit = {energia_deficit_total:.3f} kWh')
    
    ax3.set_xlabel('Fecha', fontsize=16, fontweight='bold')
    ax3.set_ylabel('Generación PV (kW)', fontsize=16, fontweight='bold')
    ax3.legend(fontsize=14)
    ax3.grid(True, alpha=0.5)
    ax3.set_xlim(0, 24)
    
    # Formatear eje x para mostrar horas
    hora_labels = [f"{int(h):02d}:00" for h in range(0, 25, 2)]
    hora_ticks = list(range(0, 25, 2))
    
    # Solo aplicar formato al último eje (ax3)
    ax3.set_xticks(hora_ticks)
    ax3.set_xticklabels(hora_labels, rotation=45, fontsize=14)
    
    # Configuración general
    plt.xlabel('Fecha', fontsize=16, fontweight='bold')
    plt.suptitle(f'Sistema Fotovoltaico - {estacion.title()}', fontsize=20, fontweight='bold', y=0.98)
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
    # CORREGIR: Los datos están en resolución de media hora, pero representan valores promedio
    # Para energía acumulada: usar factor de 0.5h por intervalo (correcto para integral)
    df_csv['Energia_GHI_Acumulada_Wh'] = np.cumsum(df_csv['GHI_W_m2'] * 0.5)  # 0.5h por intervalo
    df_csv['Energia_Gmod_Acumulada_Wh'] = np.cumsum(df_csv['Gmod'] * 0.5)
    df_csv['Energia_PV_Acumulada_Wh'] = np.cumsum(df_csv['Generacion_PV'] * 0.5)
    # CORREGIR: Calcular energía de consumo acumulada correctamente
    # Usar los valores reales de consumo multiplicados por 0.5h por intervalo
    df_csv['Energia_Consumo_Acumulada_Wh'] = np.cumsum(df_csv['Consumo'] * 0.5)
    
    print(f"\n📊 ENERGÍAS ACUMULADAS (CORREGIDAS):")
    print(f"   Energía GHI acumulada final: {df_csv['Energia_GHI_Acumulada_Wh'].iloc[-1]:.1f} Wh")
    print(f"   Energía Gmod acumulada final: {df_csv['Energia_Gmod_Acumulada_Wh'].iloc[-1]:.1f} Wh")
    print(f"   Energía PV acumulada final: {df_csv['Energia_PV_Acumulada_Wh'].iloc[-1]:.1f} Wh")
    print(f"   Energía Consumo acumulada final: {df_csv['Energia_Consumo_Acumulada_Wh'].iloc[-1]:.1f} Wh")
    
    # Reordenar columnas para mejor legibilidad
    columnas_ordenadas = [
        'Hora',
        'GHI_W_m2', 
        'Gmod',
        'Generacion_PV',
        'Consumo',
        'Diferencia_Energia_kW',
        'Exceso_Energia_kW', 
        'Deficit_Energia_kW',
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
    
    # Verificar que todas las columnas existan antes de reordenar
    columnas_existentes = [col for col in columnas_ordenadas if col in df_csv.columns]
    columnas_faltantes = [col for col in columnas_ordenadas if col not in df_csv.columns]
    
    if columnas_faltantes:
        print(f"⚠️  ADVERTENCIA: Columnas faltantes en CSV: {columnas_faltantes}")
        print(f"   Columnas disponibles: {list(df_csv.columns)}")
    
    df_csv = df_csv[columnas_existentes]
    
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
    print(f"• Energía solar disponible (GHI): {energia_ghi_total:.2f} kWh/m²·día")
    print(f"• Energía solar inclinada (Gmod): {energia_gmod_total:.2f} kWh/m²·día")
    print(f"• Generación fotovoltaica total: {energia_pv_total:.2f} kWh/día")
    print(f"• Consumo total: {energia_consumo_total:.2f} kWh/día")
    print(f"• Energía excedente: {energia_exceso_total:.2f} kWh/día")
    print(f"• Energía déficit: {energia_deficit_total:.2f} kWh/día")
    print(f"• Energía diaria requerida para baterías: {energia_deficit_total:.2f} kWh/día")
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