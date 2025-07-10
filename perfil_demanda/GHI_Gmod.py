#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para procesar y graficar datos TMY de Antofagasta
Autor: Nicole Torres
Fecha: 2024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo de gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class ProcesadorTMY:
    """Clase para procesar archivos TMY (Typical Meteorological Year)"""
    
    def __init__(self, archivo_csv):
        """
        Inicializar el procesador
        
        Args:
            archivo_csv (str): Ruta al archivo CSV con datos TMY
        """
        self.archivo_csv = archivo_csv
        self.datos = None
        self.metadatos = {}
        
    def scanner_archivo(self):
        """Realizar un escaneo completo del archivo para entender su estructura"""
        print("🔍 ESCANEANDO ARCHIVO TMY...")
        print("=" * 60)
        
        # Contar líneas totales
        with open(self.archivo_csv, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        total_lineas = len(lineas)
        print(f"📊 Total de líneas en el archivo: {total_lineas}")
        
        # Analizar metadatos (líneas 1-25)
        print("\n📋 METADATOS DEL ARCHIVO:")
        print("-" * 40)
        
        for i, linea in enumerate(lineas[:25], 1):
            linea = linea.strip()
            if linea and not linea.startswith('-') and not linea.startswith('"'):
                if ',' in linea:
                    partes = linea.split(',', 1)  # Solo dividir en la primera coma
                    if len(partes) == 2:
                        clave, valor = partes
                        print(f"  {clave}: {valor}")
                        self.metadatos[clave] = valor
        
        # Analizar variables (líneas 26-38)
        print("\n📊 VARIABLES DISPONIBLES:")
        print("-" * 40)
        
        for i, linea in enumerate(lineas[25:38], 26):
            linea = linea.strip()
            if linea and not linea.startswith('-') and not linea.startswith('"'):
                if ',' in linea:
                    partes = linea.split(',')
                    if len(partes) >= 3:
                        variable = partes[0]
                        unidad = partes[1]
                        descripcion = ','.join(partes[2:])  # Unir el resto como descripción
                        print(f"  {variable}: {unidad} - {descripcion}")
        
        # Encontrar línea de encabezados
        encabezados_linea = None
        for i, linea in enumerate(lineas[38:50], 39):
            if 'Fecha/Hora' in linea:
                encabezados_linea = i
                break
        
        if encabezados_linea:
            print(f"\n📅 Línea de encabezados encontrada: {encabezados_linea}")
            encabezados = lineas[encabezados_linea-1].strip().split(',')
            print(f"📋 Columnas disponibles: {len(encabezados)}")
            for j, col in enumerate(encabezados):
                print(f"  {j+1:2d}. {col}")
        
        # Analizar rango de fechas
        datos_inicio = encabezados_linea
        primera_fecha = lineas[datos_inicio].split(',')[0]
        ultima_fecha = lineas[-1].split(',')[0]
        
        print(f"\n📅 RANGO DE FECHAS:")
        print(f"  Inicio: {primera_fecha}")
        print(f"  Fin: {ultima_fecha}")
        
        # Contar registros de datos
        registros_datos = total_lineas - datos_inicio
        print(f"\n📊 REGISTROS DE DATOS:")
        print(f"  Total de registros: {registros_datos}")
        print(f"  Horas por día: {registros_datos / 365:.1f}")
        
        return {
            'total_lineas': total_lineas,
            'linea_encabezados': encabezados_linea,
            'registros_datos': registros_datos,
            'primera_fecha': primera_fecha,
            'ultima_fecha': ultima_fecha
        }
    
    def cargar_datos(self):
        """Cargar los datos del archivo CSV"""
        print("\n📥 CARGANDO DATOS...")
        
        # Leer datos directamente (saltando metadatos y línea de encabezados)
        # Usar engine='python' para manejar mejor el formato
        self.datos = pd.read_csv(self.archivo_csv, skiprows=41, encoding='utf-8', engine='python')
        
        # Convertir fecha a datetime
        self.datos['fecha_tmy'] = pd.to_datetime(self.datos['Fecha/Hora'])
        
        # Calcular Gmod inclinado a 35°
        print("🔧 Calculando Gmod inclinado a 35°...")
        self.datos['gmod_35'] = self.calcular_gmod_inclinado(
            self.datos['ghi'].values, 
            self.datos['fecha_tmy'].values, 
            latitud=-23.14, 
            beta=35
        )
        
        print(f"✅ Datos cargados exitosamente: {len(self.datos)} registros")
        print(f"📅 Período: {self.datos['fecha_tmy'].min()} a {self.datos['fecha_tmy'].max()}")
        print(f"📊 Variables disponibles: {list(self.datos.columns)}")
        
        return self.datos
    
    def procesar_datos(self):
        """Procesar y limpiar los datos"""
        print("\n🔧 PROCESANDO DATOS...")
        
        # Convertir columna de fecha
        self.datos['Fecha/Hora'] = pd.to_datetime(self.datos['Fecha/Hora'])
        
        # Crear columnas adicionales para facilitar el análisis
        self.datos['año'] = self.datos['Fecha/Hora'].dt.year
        self.datos['mes'] = self.datos['Fecha/Hora'].dt.month
        self.datos['dia'] = self.datos['Fecha/Hora'].dt.day
        self.datos['hora'] = self.datos['Fecha/Hora'].dt.hour
        self.datos['dia_año'] = self.datos['Fecha/Hora'].dt.dayofyear
        
        # Crear fecha sintética para TMY (año 2000 para visualización continua)
        self.datos['fecha_tmy'] = pd.to_datetime(
            self.datos['Fecha/Hora'].dt.strftime('2000-%m-%d %H:%M:%S')
        )
        
        # Verificar datos faltantes
        datos_faltantes = self.datos[['ghi', 'glb', 'temp']].isnull().sum()
        print(f"📊 Datos faltantes:")
        print(f"   GHI: {datos_faltantes['ghi']}")
        print(f"   GLB: {datos_faltantes['glb']}")
        print(f"   Temperatura: {datos_faltantes['temp']}")
        
        # Estadísticas básicas
        print(f"\n📈 ESTADÍSTICAS BÁSICAS:")
        print(f"   GHI - Máximo: {self.datos['ghi'].max():.1f} W/m²")
        print(f"   GHI - Promedio: {self.datos['ghi'].mean():.1f} W/m²")
        print(f"   GLB - Máximo: {self.datos['glb'].max():.1f} W/m²")
        print(f"   GLB - Promedio: {self.datos['glb'].mean():.1f} W/m²")
        
        # Estadísticas de temperatura
        print(f"\n🌡️  ESTADÍSTICAS DE TEMPERATURA:")
        print(f"   Temperatura - Máxima: {self.datos['temp'].max():.1f} °C")
        print(f"   Temperatura - Mínima: {self.datos['temp'].min():.1f} °C")
        print(f"   Temperatura - Promedio: {self.datos['temp'].mean():.1f} °C")
        
        # Encontrar fechas de temperaturas extremas
        temp_max_idx = self.datos['temp'].idxmax()
        temp_min_idx = self.datos['temp'].idxmin()
        
        fecha_temp_max = self.datos.loc[temp_max_idx, 'Fecha/Hora']
        fecha_temp_min = self.datos.loc[temp_min_idx, 'Fecha/Hora']
        
        print(f"   Temperatura máxima registrada: {self.datos['temp'].max():.1f} °C el {fecha_temp_max.strftime('%d/%m/%Y a las %H:%M')}")
        print(f"   Temperatura mínima registrada: {self.datos['temp'].min():.1f} °C el {fecha_temp_min.strftime('%d/%m/%Y a las %H:%M')}")
        
        return self.datos
    
    def graficar_radiacion_anual(self, guardar_grafico=True):
        """Graficar radiación GHI y Gmod para un año completo"""
        print("\n📊 GENERANDO GRÁFICO ANUAL...")
        
        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Gráfico 1: Radiación GHI (Global Horizontal)
        ax1.plot(self.datos['fecha_tmy'], self.datos['ghi'], 
                color='orange', linewidth=0.8, alpha=0.7, label='GHI (Global Horizontal)')
        ax1.set_title('Radiación Solar Global Horizontal (GHI) - TMY Antofagasta', 
                     fontsize=16, fontweight='bold')
        ax1.set_ylabel('Radiación (W/m²)', fontsize=12)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        
        # Gráfico 2: Radiación Gmod inclinado a 35°
        ax2.plot(self.datos['fecha_tmy'], self.datos['gmod_35'], 
                color='blue', linewidth=0.8, alpha=0.7, label='Gmod (Inclinado 35°)')
        ax2.set_title('Radiación Solar Gmod Inclinado a 35° - TMY Antofagasta', 
                     fontsize=16, fontweight='bold')
        ax2.set_ylabel('Radiación (W/m²)', fontsize=12)
        ax2.set_xlabel('Mes', fontsize=12)
        ax2.legend(fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'OFFGRID/results/radiacion_solar_tmy_antofagasta.png'
            plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
            print(f"💾 Gráfico guardado como: {nombre_archivo}")
        
        plt.show()
        
        return fig
    
    def graficar_comparacion_mensual(self, guardar_grafico=True):
        """Graficar comparación mensual de radiación GHI vs GLB"""
        print("\n📊 GENERANDO GRÁFICO COMPARATIVO MENSUAL...")
        
        # Calcular estadísticas mensuales
        datos_mensuales = self.datos.groupby(self.datos['fecha_tmy'].dt.month).agg({
            'ghi': ['mean', 'max'],
            'gmod_35': ['mean', 'max'],
            'temp': ['mean', 'max', 'min']
        }).round(2)
        
        # Aplanar columnas
        datos_mensuales.columns = ['ghi_mean', 'ghi_max', 'gmod_35_mean', 'gmod_35_max', 'temp_mean', 'temp_max', 'temp_min']
        datos_mensuales = datos_mensuales.reset_index()
        
        # Mostrar estadísticas de temperatura por mes
        print(f"\n🌡️  ESTADÍSTICAS DE TEMPERATURA POR MES:")
        print("=" * 60)
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        for i, mes in enumerate(meses):
            temp_min = datos_mensuales.loc[i, 'temp_min']
            temp_max = datos_mensuales.loc[i, 'temp_max']
            temp_mean = datos_mensuales.loc[i, 'temp_mean']
            print(f"{mes}: Min={temp_min:.1f}°C, Max={temp_max:.1f}°C, Prom={temp_mean:.1f}°C")
        
        return datos_mensuales
    
    def graficar_solsticios(self, guardar_grafico=True):
        """Graficar radiación GHI y GLB para los solsticios (20 junio y 21 diciembre)"""
        print("\n📊 GENERANDO GRÁFICO DE SOLSTICIOS...")
        
        # Filtrar datos para 21 de junio y 21 de diciembre
        solsticio_verano = self.datos[
            (self.datos['mes'] == 6) & (self.datos['dia'] == 20)
        ].copy()
        
        solsticio_invierno = self.datos[
            (self.datos['mes'] == 12) & (self.datos['dia'] == 21)
        ].copy()
        
        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Gráfico 1: Solsticio de Verano (20 de Junio)
        horas_verano = solsticio_verano['hora']
        ax1.plot(horas_verano, solsticio_verano['ghi'], 
                color='orange', linewidth=2, marker='o', markersize=4, 
                label='GHI (Global Horizontal)', alpha=0.8)
        ax1.plot(horas_verano, solsticio_verano['gmod_35'], 
                color='blue', linewidth=2, marker='^', markersize=4, 
                label='Gmod (Inclinado 35°)', alpha=0.8)
        
        # Encontrar y marcar máximos para verano
        ghi_max_idx_verano = solsticio_verano['ghi'].idxmax()
        gmod_max_idx_verano = solsticio_verano['gmod_35'].idxmax()
        
        ghi_max_hora_verano = solsticio_verano.loc[ghi_max_idx_verano, 'hora']
        ghi_max_valor_verano = solsticio_verano.loc[ghi_max_idx_verano, 'ghi']
        gmod_max_hora_verano = solsticio_verano.loc[gmod_max_idx_verano, 'hora']
        gmod_max_valor_verano = solsticio_verano.loc[gmod_max_idx_verano, 'gmod_35']
        
        # Agregar flechas para máximos (posicionadas hacia abajo para evitar superposición)
        ax1.annotate(f'GHI máx\n{ghi_max_valor_verano:.0f} W/m²', 
                    xy=(ghi_max_hora_verano, ghi_max_valor_verano),
                    xytext=(ghi_max_hora_verano - 2, ghi_max_valor_verano - 200),
                    arrowprops=dict(arrowstyle='->', color='orange', lw=2),
                    fontsize=11, color='orange', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        ax1.annotate(f'Gmod máx\n{gmod_max_valor_verano:.0f} W/m²', 
                    xy=(gmod_max_hora_verano, gmod_max_valor_verano),
                    xytext=(gmod_max_hora_verano - 2, gmod_max_valor_verano - 200),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2),
                    fontsize=11, color='blue', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        ax1.set_title('Día de Invierno - 20 de Junio', 
                     fontsize=17, fontweight='bold')
        ax1.set_ylabel('Radiación (W/m²)', fontsize=13)
        ax1.set_xlabel('Hora del día', fontsize=13)
        ax1.set_xticks(range(0, 24, 2))
        ax1.tick_params(axis='both', which='major', labelsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=12)
        ax1.set_xlim(0, 23)
        
        # Agregar estadísticas del día
        ghi_max_verano = solsticio_verano['ghi'].max()
        gmod_max_verano = solsticio_verano['gmod_35'].max()
        # CORREGIDO: energía diaria en kWh/m²
        ghi_energia_verano = solsticio_verano['ghi'].sum() / 1000  # kWh/m²
        gmod_energia_verano = solsticio_verano['gmod_35'].sum() / 1000  # kWh/m²
        
        ax1.text(0.02, 0.98, f'GHI máx: {ghi_max_verano:.0f} W/m²\nGmod máx: {gmod_max_verano:.0f} W/m²\nEnergía GHI: {ghi_energia_verano:.2f} kWh/m²\nEnergía Gmod: {gmod_energia_verano:.2f} kWh/m²', 
                transform=ax1.transAxes, verticalalignment='top', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Gráfico 2: Solsticio de Invierno (21 de Diciembre)
        horas_invierno = solsticio_invierno['hora']
        ax2.plot(horas_invierno, solsticio_invierno['ghi'], 
                color='orange', linewidth=2, marker='o', markersize=4, 
                label='GHI (Global Horizontal)', alpha=0.8)
        ax2.plot(horas_invierno, solsticio_invierno['gmod_35'], 
                color='blue', linewidth=2, marker='^', markersize=4, 
                label='Gmod (Inclinado 35°)', alpha=0.8)
        
        # Encontrar y marcar máximos para invierno
        ghi_max_idx_invierno = solsticio_invierno['ghi'].idxmax()
        gmod_max_idx_invierno = solsticio_invierno['gmod_35'].idxmax()
        
        ghi_max_hora_invierno = solsticio_invierno.loc[ghi_max_idx_invierno, 'hora']
        ghi_max_valor_invierno = solsticio_invierno.loc[ghi_max_idx_invierno, 'ghi']
        gmod_max_hora_invierno = solsticio_invierno.loc[gmod_max_idx_invierno, 'hora']
        gmod_max_valor_invierno = solsticio_invierno.loc[gmod_max_idx_invierno, 'gmod_35']
        
        # Agregar flechas para máximos (posicionadas hacia abajo para evitar superposición)
        ax2.annotate(f'GHI máx\n{ghi_max_valor_invierno:.0f} W/m²', 
                    xy=(ghi_max_hora_invierno, ghi_max_valor_invierno),
                    xytext=(ghi_max_hora_invierno - 3, ghi_max_valor_invierno - 300),
                    arrowprops=dict(arrowstyle='->', color='orange', lw=2),
                    fontsize=11, color='orange', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        ax2.annotate(f'Gmod máx\n{gmod_max_valor_invierno:.0f} W/m²', 
                    xy=(gmod_max_hora_invierno, gmod_max_valor_invierno),
                    xytext=(gmod_max_hora_invierno + 3, gmod_max_valor_invierno - 300),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2),
                    fontsize=11, color='blue', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        ax2.set_title('Día de Verano - 21 de Diciembre', 
                     fontsize=17, fontweight='bold')
        ax2.set_ylabel('Radiación (W/m²)', fontsize=13)
        ax2.set_xlabel('Hora del día', fontsize=13)
        ax2.set_xticks(range(0, 24, 2))
        ax2.tick_params(axis='both', which='major', labelsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=12)
        ax2.set_xlim(0, 23)
        
        # Agregar estadísticas del día
        ghi_max_invierno = solsticio_invierno['ghi'].max()
        gmod_max_invierno = solsticio_invierno['gmod_35'].max()
        # CORREGIDO: energía diaria en kWh/m²
        ghi_energia_invierno = solsticio_invierno['ghi'].sum() / 1000  # kWh/m²
        gmod_energia_invierno = solsticio_invierno['gmod_35'].sum() / 1000  # kWh/m²
        
        ax2.text(0.02, 0.98, f'GHI máx: {ghi_max_invierno:.0f} W/m²\nGmod máx: {gmod_max_invierno:.0f} W/m²\nEnergía GHI: {ghi_energia_invierno:.2f} kWh/m²\nEnergía Gmod: {gmod_energia_invierno:.2f} kWh/m²', 
                transform=ax2.transAxes, verticalalignment='top', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'OFFGRID/results/solsticios_tmy_antofagasta.png'
            plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
            print(f"💾 Gráfico guardado como: {nombre_archivo}")
        
        plt.show()
        
        # Imprimir comparación
        print(f"\n📊 COMPARACIÓN DE SOLSTICIOS:")
        print("=" * 50)
        print(f"🌞 20 de Junio (Día de Invierno - Solsticio de Invierno):")
        print(f"   GHI máximo: {ghi_max_verano:.0f} W/m² a las {ghi_max_hora_verano}:00")
        print(f"   Gmod máximo: {gmod_max_verano:.0f} W/m² a las {gmod_max_hora_verano}:00")
        print(f"   Energía GHI: {ghi_energia_verano:.2f} kWh/m²")
        print(f"   Energía Gmod: {gmod_energia_verano:.2f} kWh/m²")
        print(f"   Horas de luz: {len(solsticio_verano[solsticio_verano['ghi'] > 0])}")
        
        print(f"\n🌞 21 de Diciembre (Día de Verano - Solsticio de Verano):")
        print(f"   GHI máximo: {ghi_max_invierno:.0f} W/m² a las {ghi_max_hora_invierno}:00")
        print(f"   Gmod máximo: {gmod_max_invierno:.0f} W/m² a las {gmod_max_hora_invierno}:00")
        print(f"   Energía GHI: {ghi_energia_invierno:.2f} kWh/m²")
        print(f"   Energía Gmod: {gmod_energia_invierno:.2f} kWh/m²")
        print(f"   Horas de luz: {len(solsticio_invierno[solsticio_invierno['ghi'] > 0])}")
        
        print(f"\n📈 DIFERENCIAS:")
        print(f"   Energía adicional en verano: {ghi_energia_invierno - ghi_energia_verano:.2f} kWh/m²")
        print(f"   Factor de mejora en verano: {ghi_energia_invierno / ghi_energia_verano:.2f}x")
        
        return fig, {
            'solsticio_verano': solsticio_verano,
            'solsticio_invierno': solsticio_invierno,
            'stats_verano': {
                'ghi_max': ghi_max_verano,
                'gmod_max': gmod_max_verano,
                'ghi_energia': ghi_energia_verano,
                'gmod_energia': gmod_energia_verano,
                'ghi_max_hora': ghi_max_hora_verano,
                'gmod_max_hora': gmod_max_hora_verano
            },
            'stats_invierno': {
                'ghi_max': ghi_max_invierno,
                'gmod_max': gmod_max_invierno,
                'ghi_energia': ghi_energia_invierno,
                'gmod_energia': gmod_energia_invierno,
                'ghi_max_hora': ghi_max_hora_invierno,
                'gmod_max_hora': gmod_max_hora_invierno
            }
        }
    
    def generar_reporte(self):
        """Generar un reporte completo de los datos"""
        print("\n📋 GENERANDO REPORTE...")
        
        # Calcular estadísticas
        ghi_stats = {
            'media': self.datos['ghi'].mean(),
            'max': self.datos['ghi'].max(),
            'min': self.datos['ghi'].min(),
            'std': self.datos['ghi'].std()
        }
        
        gmod_stats = {
            'media': self.datos['gmod_35'].mean(),
            'max': self.datos['gmod_35'].max(),
            'min': self.datos['gmod_35'].min(),
            'std': self.datos['gmod_35'].std()
        }
        
        # Calcular energía anual (kWh/m²)
        # Los datos TMY están en W/m² como valores promedio por hora
        energia_ghi_anual = self.datos['ghi'].sum() / 1000  # kWh/m²
        energia_gmod_anual = self.datos['gmod_35'].sum() / 1000  # kWh/m²
        
        # Generar reporte
        reporte = f"""
        ========================================
        REPORTE DE RADIACIÓN SOLAR - TMY ANTOFAGASTA
        ========================================
        
        PERÍODO: {self.datos['fecha_tmy'].min().strftime('%Y-%m-%d')} a {self.datos['fecha_tmy'].max().strftime('%Y-%m-%d')}
        TOTAL DE REGISTROS: {len(self.datos)} horas
        
        ESTADÍSTICAS GHI (Global Horizontal):
        - Media: {ghi_stats['media']:.2f} W/m²
        - Máximo: {ghi_stats['max']:.2f} W/m²
        - Mínimo: {ghi_stats['min']:.2f} W/m²
        - Desviación estándar: {ghi_stats['std']:.2f} W/m²
        - Energía anual: {energia_ghi_anual:.2f} kWh/m²
        
        ESTADÍSTICAS GMOD (Inclinado 35°):
        - Media: {gmod_stats['media']:.2f} W/m²
        - Máximo: {gmod_stats['max']:.2f} W/m²
        - Mínimo: {gmod_stats['min']:.2f} W/m²
        - Desviación estándar: {gmod_stats['std']:.2f} W/m²
        - Energía anual: {energia_gmod_anual:.2f} kWh/m²
        
        COMPARACIÓN:
        - Gmod vs GHI: {((gmod_stats['media'] - ghi_stats['media']) / ghi_stats['media'] * 100):.1f}% de mejora
        - Energía adicional Gmod vs GHI: {energia_gmod_anual - energia_ghi_anual:.2f} kWh/m²/año
        
        ========================================
        """
        
        return reporte

    def exportar_dias_a_excel(self, dias_seleccionados=None, nombre_archivo=None, incluir_estadisticas=True):
        """
        Exporta los datos de irradiancia de días seleccionados a un archivo Excel
        
        Args:
            dias_seleccionados (list): Lista de tuplas (mes, dia) ej: [(6, 20), (12, 21)]
                                     Si es None, exporta días representativos por defecto
            nombre_archivo (str): Nombre del archivo Excel. Si es None, se genera automáticamente
            incluir_estadisticas (bool): Si incluir una hoja con estadísticas
        
        Returns:
            str: Nombre del archivo generado
        """
        print("\n📊 GENERANDO ARCHIVO EXCEL CON DATOS DE IRRADIANCIA...")
        
        # Días por defecto si no se especifican
        if dias_seleccionados is None:
            dias_seleccionados = [
                (6, 20),   # Solsticio de invierno
                (12, 21)   # Día representativo de julio
            ]
        
        # Generar nombre de archivo si no se proporciona
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f'OFFGRID/data/Recurso_solar.xlsx'
        
        # Crear diccionario para almacenar datos de cada día
        datos_dias = {}
        nombres_dias = {
            (6, 20): "Solsticio_Invierno_20Jun",
            (12, 21): "Solsticio_Verano_21Dic"
        }
        
        # Extraer datos para cada día seleccionado
        for mes, dia in dias_seleccionados:
            # Filtrar datos para el día específico
            datos_dia = self.datos[
                (self.datos['mes'] == mes) & (self.datos['dia'] == dia)
            ].copy()
            
            if len(datos_dia) > 0:
                # Preparar datos para Excel
                datos_exportar = pd.DataFrame({
                    'Hora': datos_dia['hora'],
                    'Fecha_Hora': datos_dia['Fecha/Hora'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'GHI_W_m2': datos_dia['ghi'].round(2),
                    'Gmod': datos_dia['gmod_35'].round(2),
                    'Porcentaje_Mejora': ((datos_dia['gmod_35'] - datos_dia['ghi']) / datos_dia['ghi'] * 100).round(2)
                })
                
                # Generar nombre de hoja
                nombre_hoja = nombres_dias.get((mes, dia), f"{mes:02d}_{dia:02d}")
                datos_dias[nombre_hoja] = datos_exportar
                
                print(f"   ✅ Datos extraídos para {dia}/{mes}: {len(datos_exportar)} registros")
            else:
                print(f"   ⚠️  No se encontraron datos para {dia}/{mes}")
        
        # Crear archivo Excel con múltiples hojas
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            
            # Escribir datos de cada día en hojas separadas
            for nombre_hoja, datos_dia in datos_dias.items():
                datos_dia.to_excel(writer, sheet_name=nombre_hoja, index=False)
                
                # Obtener la hoja para formatear
                worksheet = writer.sheets[nombre_hoja]
                
                # Ajustar ancho de columnas
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 25)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Crear hoja de resumen si se solicita
            if incluir_estadisticas:
                resumen_datos = []
                
                for nombre_hoja, datos_dia in datos_dias.items():
                    # Calcular estadísticas del día
                    ghi_max = datos_dia['GHI_W_m2'].max()
                    ghi_promedio = datos_dia['GHI_W_m2'].mean()
                    # Calcular energía diaria (valores horarios en W/m²)
                    ghi_energia = datos_dia['GHI_W_m2'].sum() / 1000  # kWh/m²
                    
                    gmod_max = datos_dia['Gmod'].max()
                    gmod_promedio = datos_dia['Gmod'].mean()
                    gmod_energia = datos_dia['Gmod'].sum() / 1000  # kWh/m²
                    
                    hora_max_ghi = datos_dia.loc[datos_dia['GHI_W_m2'].idxmax(), 'Hora']
                    hora_max_gmod = datos_dia.loc[datos_dia['Gmod'].idxmax(), 'Hora']
                    
                    horas_sol = len(datos_dia[datos_dia['GHI_W_m2'] > 0])
                    mejora_energia = ((gmod_energia - ghi_energia) / ghi_energia * 100)
                    
                    resumen_datos.append({
                        'Día': nombre_hoja,
                        'GHI_Max_W_m2': round(ghi_max, 2),
                        'GHI_Promedio_W_m2': round(ghi_promedio, 2),
                        'GHI_Energia_kWh_m2': round(ghi_energia, 3),
                        'Hora_Max_GHI': int(hora_max_ghi),
                        'Gmod_Max_W_m2': round(gmod_max, 2),
                        'Gmod_Promedio_W_m2': round(gmod_promedio, 2),
                        'Gmod_Energia_kWh_m2': round(gmod_energia, 3),
                        'Hora_Max_Gmod': int(hora_max_gmod),
                        'Horas_Sol': horas_sol,
                        'Mejora_Energia_%': round(mejora_energia, 2),
                        'Energia_Adicional_kWh_m2': round(gmod_energia - ghi_energia, 3)
                    })
                
                # Crear DataFrame de resumen
                df_resumen = pd.DataFrame(resumen_datos)
                df_resumen.to_excel(writer, sheet_name='Resumen_Estadisticas', index=False)
                
                # Formatear hoja de resumen
                worksheet_resumen = writer.sheets['Resumen_Estadisticas']
                for column in worksheet_resumen.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 30)
                    worksheet_resumen.column_dimensions[column_letter].width = adjusted_width
            
            # Crear hoja de información general
            info_general = pd.DataFrame({
                'Parámetro': [
                    'Ubicación',
                    'Latitud',
                    'Inclinación Gmod',
                    'Período TMY',
                    'Total Registros',
                    'Archivo Fuente',
                    'Fecha Generación'
                ],
                'Valor': [
                    'Antofagasta, Chile',
                    '-23.14°',
                    '35°',
                    f"{self.datos['fecha_tmy'].min().strftime('%Y-%m-%d')} a {self.datos['fecha_tmy'].max().strftime('%Y-%m-%d')}",
                    f"{len(self.datos)} horas",
                    self.archivo_csv,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            })
            
            info_general.to_excel(writer, sheet_name='Informacion_General', index=False)
            
            # Formatear hoja de información
            worksheet_info = writer.sheets['Informacion_General']
            worksheet_info.column_dimensions['A'].width = 25
            worksheet_info.column_dimensions['B'].width = 40
        
        print(f"✅ Archivo Excel generado exitosamente: {nombre_archivo}")
        print(f"📊 Hojas incluidas: {len(datos_dias)} días + Resumen + Información General")
        
        # Mostrar resumen de lo exportado
        print(f"\n📋 RESUMEN DE EXPORTACIÓN:")
        print("=" * 50)
        for nombre_hoja, datos_dia in datos_dias.items():
            # Calcular energía diaria (valores horarios en W/m²)
            energia_ghi = datos_dia['GHI_W_m2'].sum() / 1000
            energia_gmod = datos_dia['Gmod'].sum() / 1000
            print(f"📅 {nombre_hoja}:")
            print(f"   - GHI máximo: {datos_dia['GHI_W_m2'].max():.0f} W/m²")
            print(f"   - Gmod máximo: {datos_dia['Gmod'].max():.0f} W/m²")
            print(f"   - Energía GHI: {energia_ghi:.3f} kWh/m²")
            print(f"   - Energía Gmod: {energia_gmod:.3f} kWh/m²")
            print(f"   - Mejora: {((energia_gmod - energia_ghi) / energia_ghi * 100):.1f}%")
        
        return nombre_archivo

    def calcular_gmod_inclinado(self, ghi_data, fechas, latitud=-23.14, beta=35):
        """
        Calcula Gmod inclinado usando la fórmula física:
        Gmod = GHI × (cos(θ) / cos(θz))
        donde θz es el ángulo cenital solar y θ el ángulo de incidencia en el panel inclinado.
        """
        import numpy as np
        import pandas as pd

        # Convertir fechas a datetime si es necesario
        if isinstance(fechas[0], np.datetime64):
            fechas_dt = pd.to_datetime(fechas)
        else:
            fechas_dt = fechas

        # Día del año y hora decimal
        dias_año = np.array([fecha.timetuple().tm_yday for fecha in fechas_dt])
        horas = np.array([fecha.hour + fecha.minute/60.0 for fecha in fechas_dt])

        # Declinación solar (radianes)
        declinacion = 23.45 * np.sin(np.deg2rad((284 + dias_año) * 360 / 365))
        declinacion_rad = np.deg2rad(declinacion)

        # Ángulo horario (radianes)
        H = np.deg2rad(15 * (horas - 12))

        # Latitud y beta en radianes
        lat_rad = np.deg2rad(latitud)
        beta_rad = np.deg2rad(beta)

        # Ángulo cenital solar (θz)
        cos_zenital = (np.sin(lat_rad) * np.sin(declinacion_rad) +
                       np.cos(lat_rad) * np.cos(declinacion_rad) * np.cos(H))
        cos_zenital = np.clip(cos_zenital, 0, 1)  # Evitar valores negativos
        # theta_z_rad = np.arccos(cos_zenital)  # No se usa directamente

        # Ángulo de incidencia en el panel (θ)
        # Para panel orientado al norte (azimut = 0)
        cos_theta = (np.sin(lat_rad) * np.sin(declinacion_rad) * np.cos(beta_rad) -
                     np.sin(lat_rad) * np.cos(declinacion_rad) * np.cos(H) * np.sin(beta_rad) +
                     np.cos(lat_rad) * np.cos(declinacion_rad) * np.cos(H) * np.cos(beta_rad) +
                     np.cos(lat_rad) * np.sin(declinacion_rad) * np.sin(beta_rad))
        cos_theta = np.clip(cos_theta, 0, 1)
        # theta_rad = np.arccos(cos_theta)  # No se usa directamente

        # Factor de transposición
        factor = np.zeros_like(ghi_data)
        mask = cos_zenital > 0.01
        factor[mask] = cos_theta[mask] / cos_zenital[mask]
        factor = np.clip(factor, 0, 3)  # Limitar valores extremos

        # Calcular Gmod
        gmod = ghi_data * factor
        gmod = np.where(cos_zenital > 0.01, gmod, 0)

        return gmod

    def calcular_temperaturas_horas_luz(self):
        """
        Calcula las temperaturas mínima y máxima durante las horas de luz
        (cuando GHI > 0)
        """
        print("\n🌡️☀️ CALCULANDO TEMPERATURAS DURANTE HORAS DE LUZ...")
        
        # Filtrar solo los datos con radiación solar (horas de luz)
        datos_luz = self.datos[self.datos['ghi'] > 0].copy()
        
        if len(datos_luz) == 0:
            print("⚠️  No se encontraron datos con radiación solar")
            return None
        
        # Calcular estadísticas de temperatura durante horas de luz
        temp_max_luz = datos_luz['temp'].max()
        temp_min_luz = datos_luz['temp'].min()
        temp_prom_luz = datos_luz['temp'].mean()
        
        # Encontrar fechas y horas de temperaturas extremas durante horas de luz
        temp_max_idx = datos_luz['temp'].idxmax()
        temp_min_idx = datos_luz['temp'].idxmin()
        
        fecha_temp_max = datos_luz.loc[temp_max_idx, 'Fecha/Hora']
        fecha_temp_min = datos_luz.loc[temp_min_idx, 'Fecha/Hora']
        ghi_temp_max = datos_luz.loc[temp_max_idx, 'ghi']
        ghi_temp_min = datos_luz.loc[temp_min_idx, 'ghi']
        
        # Mostrar resultados
        print("=" * 70)
        print(f"📊 ESTADÍSTICAS DE TEMPERATURAS DURANTE HORAS DE LUZ:")
        print(f"   Total de horas de luz: {len(datos_luz)} horas")
        print(f"   Porcentaje del año: {len(datos_luz)/len(self.datos)*100:.1f}%")
        print()
        print(f"🌡️  TEMPERATURA MÁXIMA DURANTE HORAS DE LUZ:")
        print(f"   Valor: {temp_max_luz:.1f} °C")
        print(f"   Fecha: {fecha_temp_max.strftime('%d/%m/%Y a las %H:%M')}")
        print(f"   Radiación GHI en ese momento: {ghi_temp_max:.1f} W/m²")
        print()
        print(f"🌡️  TEMPERATURA MÍNIMA DURANTE HORAS DE LUZ:")
        print(f"   Valor: {temp_min_luz:.1f} °C")
        print(f"   Fecha: {fecha_temp_min.strftime('%d/%m/%Y a las %H:%M')}")
        print(f"   Radiación GHI en ese momento: {ghi_temp_min:.1f} W/m²")
        print()
        print(f"📈 ESTADÍSTICAS ADICIONALES:")
        print(f"   Temperatura promedio durante horas de luz: {temp_prom_luz:.1f} °C")
        print(f"   Rango térmico durante horas de luz: {temp_max_luz - temp_min_luz:.1f} °C")
        print("=" * 70)
        
        # Comparar con temperaturas generales
        temp_max_general = self.datos['temp'].max()
        temp_min_general = self.datos['temp'].min()
        
        print(f"\n🔍 COMPARACIÓN CON TEMPERATURAS GENERALES (24 horas):")
        print(f"   Temperatura máxima general: {temp_max_general:.1f} °C")
        print(f"   Temperatura máxima en horas de luz: {temp_max_luz:.1f} °C")
        print(f"   Diferencia: {temp_max_general - temp_max_luz:.1f} °C")
        print()
        print(f"   Temperatura mínima general: {temp_min_general:.1f} °C")
        print(f"   Temperatura mínima en horas de luz: {temp_min_luz:.1f} °C")
        print(f"   Diferencia: {temp_min_luz - temp_min_general:.1f} °C")
        
        return {
            'temp_max_luz': temp_max_luz,
            'temp_min_luz': temp_min_luz,
            'temp_prom_luz': temp_prom_luz,
            'fecha_temp_max': fecha_temp_max,
            'fecha_temp_min': fecha_temp_min,
            'ghi_temp_max': ghi_temp_max,
            'ghi_temp_min': ghi_temp_min,
            'horas_luz': len(datos_luz),
            'porcentaje_luz': len(datos_luz)/len(self.datos)*100
        }

    def calcular_ghi_diario_solsticios(self):
        """
        Calcula el GHI diario total para los solsticios (20 junio y 21 diciembre)
        """
        print("\n☀️📊 CALCULANDO GHI DIARIO DE LOS SOLSTICIOS...")
        
        # Filtrar datos para 20 de junio (solsticio de invierno)
        solsticio_invierno = self.datos[
            (self.datos['mes'] == 6) & (self.datos['dia'] == 20)
        ].copy()
        
        # Filtrar datos para 21 de diciembre (solsticio de verano)
        solsticio_verano = self.datos[
            (self.datos['mes'] == 12) & (self.datos['dia'] == 21)
        ].copy()
        
        if len(solsticio_invierno) == 0 or len(solsticio_verano) == 0:
            print("⚠️  No se encontraron datos para los solsticios")
            return None
        
        # Calcular GHI diario (kWh/m²/día)
        # Los datos TMY están en W/m² como valores promedio por hora
        # Para convertir a kWh/m²: sumar valores horarios y dividir por 1000
        
        ghi_diario_invierno = solsticio_invierno['ghi'].sum() / 1000  # kWh/m²
        ghi_diario_verano = solsticio_verano['ghi'].sum() / 1000  # kWh/m²
        
        # Calcular Gmod diario también
        gmod_diario_invierno = solsticio_invierno['gmod_35'].sum() / 1000  # kWh/m²
        gmod_diario_verano = solsticio_verano['gmod_35'].sum() / 1000  # kWh/m²
        
        # Estadísticas adicionales
        horas_luz_invierno = len(solsticio_invierno[solsticio_invierno['ghi'] > 0])
        horas_luz_verano = len(solsticio_verano[solsticio_verano['ghi'] > 0])
        
        ghi_max_invierno = solsticio_invierno['ghi'].max()
        ghi_max_verano = solsticio_verano['ghi'].max()
        
        # Mostrar resultados
        print("=" * 80)
        print(f"📊 GHI DIARIO DE LOS SOLSTICIOS - TMY ANTOFAGASTA")
        print("=" * 80)
        
        print(f"\n🌞 SOLSTICIO DE INVIERNO (20 de Junio):")
        print(f"   GHI diario total: {ghi_diario_invierno:.3f} kWh/m²/día")
        print(f"   Gmod diario total: {gmod_diario_invierno:.3f} kWh/m²/día")
        print(f"   GHI máximo: {ghi_max_invierno:.1f} W/m²")
        print(f"   Horas de luz: {horas_luz_invierno} horas")
        print(f"   Promedio horario durante horas de luz: {solsticio_invierno[solsticio_invierno['ghi'] > 0]['ghi'].mean():.1f} W/m²")
        
        print(f"\n🌞 SOLSTICIO DE VERANO (21 de Diciembre):")
        print(f"   GHI diario total: {ghi_diario_verano:.3f} kWh/m²/día")
        print(f"   Gmod diario total: {gmod_diario_verano:.3f} kWh/m²/día")
        print(f"   GHI máximo: {ghi_max_verano:.1f} W/m²")
        print(f"   Horas de luz: {horas_luz_verano} horas")
        print(f"   Promedio horario durante horas de luz: {solsticio_verano[solsticio_verano['ghi'] > 0]['ghi'].mean():.1f} W/m²")
        
        # Comparación entre solsticios
        diferencia_ghi = ghi_diario_verano - ghi_diario_invierno
        factor_mejora = ghi_diario_verano / ghi_diario_invierno
        diferencia_horas = horas_luz_verano - horas_luz_invierno
        
        print(f"\n📈 COMPARACIÓN ENTRE SOLSTICIOS:")
        print(f"   Diferencia GHI diario: {diferencia_ghi:.3f} kWh/m²/día")
        print(f"   Factor de mejora (Verano/Invierno): {factor_mejora:.2f}x")
        print(f"   Incremento porcentual: {((factor_mejora - 1) * 100):.1f}%")
        print(f"   Diferencia en horas de luz: {diferencia_horas} horas")
        print(f"   Diferencia en GHI máximo: {ghi_max_verano - ghi_max_invierno:.1f} W/m²")
        
        # Equivalencias energéticas
        print(f"\n⚡ EQUIVALENCIAS ENERGÉTICAS:")
        print(f"   En verano se recibe {diferencia_ghi:.3f} kWh/m²/día adicionales")
        print(f"   Esto equivale a {diferencia_ghi * 365:.1f} kWh/m²/año si fuera constante")
        print(f"   Diferencia relativa: {((ghi_diario_verano - ghi_diario_invierno) / ghi_diario_invierno * 100):.1f}%")
        
        # Análisis de Gmod
        print(f"\n🔄 ANÁLISIS GMOD (Inclinado 35°):")
        print(f"   Gmod invierno: {gmod_diario_invierno:.3f} kWh/m²/día")
        print(f"   Gmod verano: {gmod_diario_verano:.3f} kWh/m²/día")
        print(f"   Mejora Gmod vs GHI en invierno: {((gmod_diario_invierno - ghi_diario_invierno) / ghi_diario_invierno * 100):.1f}%")
        print(f"   Mejora Gmod vs GHI en verano: {((gmod_diario_verano - ghi_diario_verano) / ghi_diario_verano * 100):.1f}%")
        
        print("=" * 80)
        
        return {
            'ghi_diario_invierno': ghi_diario_invierno,
            'ghi_diario_verano': ghi_diario_verano,
            'gmod_diario_invierno': gmod_diario_invierno,
            'gmod_diario_verano': gmod_diario_verano,
            'diferencia_ghi': diferencia_ghi,
            'factor_mejora': factor_mejora,
            'horas_luz_invierno': horas_luz_invierno,
            'horas_luz_verano': horas_luz_verano,
            'ghi_max_invierno': ghi_max_invierno,
            'ghi_max_verano': ghi_max_verano
        }

    def calcular_radiacion_teorica_cielo_despejado(self, fechas, latitud=-23.14):
        """
        Calcula la radiación solar teórica para cielo despejado usando el modelo de Iqbal
        
        Args:
            fechas: Array de fechas datetime
            latitud: Latitud en grados decimales (negativo para sur)
        
        Returns:
            Array con radiación teórica en W/m²
        """
        # Convertir fechas a array de días del año
        if isinstance(fechas[0], np.datetime64):
            fechas_dt = pd.to_datetime(fechas)
        else:
            fechas_dt = fechas
            
        # Extraer día del año y hora
        dias_año = np.array([fecha.timetuple().tm_yday for fecha in fechas_dt])
        horas = np.array([fecha.hour + fecha.minute/60.0 for fecha in fechas_dt])
        
        # Constante solar (W/m²)
        I0 = 1367
        
        # Calcular corrección por distancia Tierra-Sol
        B = (dias_año - 1) * 2 * np.pi / 365
        correcion_distancia = 1.000110 + 0.034221 * np.cos(B) + 0.001280 * np.sin(B) + \
                             0.000719 * np.cos(2*B) + 0.000077 * np.sin(2*B)
        
        # Calcular declinación solar (radianes)
        declinacion = np.deg2rad(23.45 * np.sin(np.deg2rad((284 + dias_año) * 360 / 365)))
        
        # Convertir latitud a radianes
        lat_rad = np.deg2rad(latitud)
        
        # Calcular ángulo horario (radianes)
        angulo_horario = np.deg2rad(15 * (horas - 12))
        
        # Calcular ángulo cenital solar
        cos_zenital = (np.sin(lat_rad) * np.sin(declinacion) + 
                      np.cos(lat_rad) * np.cos(declinacion) * np.cos(angulo_horario))
        
        # Evitar valores negativos (sol bajo el horizonte)
        cos_zenital = np.maximum(cos_zenital, 0)
        
        # Calcular radiación extraterrestre
        radiacion_extraterrestre = I0 * correcion_distancia * cos_zenital
        
        # Modelo simple de cielo despejado (Iqbal simplificado)
        # Coeficientes típicos para atmósfera estándar
        transmitancia_atmosferica = 0.75  # Valor típico para cielo despejado
        
        # Calcular radiación teórica de cielo despejado
        ghi_teorico = radiacion_extraterrestre * transmitancia_atmosferica
        
        # Ajustar por masa de aire (aproximación simple)
        altura_solar = np.rad2deg(np.arcsin(cos_zenital))
        masa_aire = np.where(altura_solar > 0, 1 / cos_zenital, 0)
        
        # Aplicar corrección por masa de aire
        factor_masa_aire = np.exp(-0.0001 * masa_aire)
        ghi_teorico = ghi_teorico * factor_masa_aire
        
        return ghi_teorico

    def calcular_indice_claridad(self):
        """
        Calcula el índice de claridad (clearness index) para cada registro
        Índice de claridad = GHI_observado / GHI_cielo_despejado
        
        Valores típicos:
        - > 0.7: Día despejado
        - 0.4 - 0.7: Parcialmente nuboso  
        - < 0.4: Muy nuboso
        """
        print("\n☀️🌤️ CALCULANDO ÍNDICE DE CLARIDAD...")
        
        # Calcular radiación teórica de cielo despejado
        ghi_teorico = self.calcular_radiacion_teorica_cielo_despejado(
            self.datos['Fecha/Hora'].values, 
            latitud=-23.14
        )
        
        # Agregar al DataFrame
        self.datos['ghi_teorico'] = ghi_teorico
        
        # Calcular índice de claridad
        # Evitar división por cero
        indice_claridad = np.where(ghi_teorico > 0, 
                                 self.datos['ghi'] / ghi_teorico, 
                                 0)
        
        # Limitar valores extremos (a veces puede ser > 1 por efectos de nubes)
        indice_claridad = np.clip(indice_claridad, 0, 1.2)
        
        self.datos['indice_claridad'] = indice_claridad
        
        print(f"✅ Índice de claridad calculado para {len(self.datos)} registros")
        print(f"📊 Estadísticas del índice de claridad:")
        print(f"   Promedio: {indice_claridad.mean():.3f}")
        print(f"   Máximo: {indice_claridad.max():.3f}")
        print(f"   Mínimo: {indice_claridad.min():.3f}")
        
        return indice_claridad

    def clasificar_dias_nubosos(self):
        """
        Clasifica cada día según su nivel de nubosidad usando el índice de claridad
        """
        print("\n🌤️📊 CLASIFICANDO DÍAS SEGÚN NUBOSIDAD...")
        
        # Asegurar que el índice de claridad esté calculado
        if 'indice_claridad' not in self.datos.columns:
            self.calcular_indice_claridad()
        
        # Calcular índice de claridad promedio diario (solo durante horas de luz)
        datos_luz = self.datos[self.datos['ghi'] > 0].copy()
        
        indice_diario = datos_luz.groupby([datos_luz['mes'], datos_luz['dia']]).agg({
            'indice_claridad': 'mean',
            'ghi': ['mean', 'max', 'std'],
            'ghi_teorico': 'mean'
        }).round(3)
        
        # Aplanar columnas
        indice_diario.columns = ['indice_claridad_prom', 'ghi_mean', 'ghi_max', 'ghi_std', 'ghi_teorico_mean']
        indice_diario = indice_diario.reset_index()
        
        # Clasificar días según índice de claridad
        def clasificar_dia(indice):
            if indice >= 0.7:
                return 'Despejado'
            elif indice >= 0.4:
                return 'Parcialmente nuboso'
            else:
                return 'Muy nuboso'
        
        indice_diario['clasificacion'] = indice_diario['indice_claridad_prom'].apply(clasificar_dia)
        
        # Agregar fecha legible
        indice_diario['fecha'] = pd.to_datetime(
            indice_diario.apply(lambda x: f"2000-{x['mes']:02d}-{x['dia']:02d}", axis=1)
        )
        
        # Contar días por categoría
        conteo_dias = indice_diario['clasificacion'].value_counts()
        
        print("=" * 60)
        print("📊 CLASIFICACIÓN DE DÍAS POR NUBOSIDAD - TMY ANTOFAGASTA")
        print("=" * 60)
        
        for categoria, cantidad in conteo_dias.items():
            porcentaje = (cantidad / len(indice_diario)) * 100
            print(f"☀️ {categoria}: {cantidad} días ({porcentaje:.1f}%)")
        
        # Mostrar ejemplos de cada categoría
        print(f"\n📅 EJEMPLOS DE CADA CATEGORÍA:")
        print("-" * 50)
        
        for categoria in ['Despejado', 'Parcialmente nuboso', 'Muy nuboso']:
            dias_categoria = indice_diario[indice_diario['clasificacion'] == categoria]
            if len(dias_categoria) > 0:
                # Mostrar el más extremo de cada categoría
                if categoria == 'Despejado':
                    ejemplo = dias_categoria.loc[dias_categoria['indice_claridad_prom'].idxmax()]
                else:
                    ejemplo = dias_categoria.loc[dias_categoria['indice_claridad_prom'].idxmin()]
                
                print(f"\n🌤️ {categoria}:")
                print(f"   Fecha: {ejemplo['fecha'].strftime('%d/%m')}")
                print(f"   Índice de claridad: {ejemplo['indice_claridad_prom']:.3f}")
                print(f"   GHI promedio: {ejemplo['ghi_mean']:.1f} W/m²")
                print(f"   GHI máximo: {ejemplo['ghi_max']:.1f} W/m²")
                print(f"   GHI teórico: {ejemplo['ghi_teorico_mean']:.1f} W/m²")
        
        # Análisis estacional
        print(f"\n📈 ANÁLISIS ESTACIONAL:")
        print("-" * 40)
        
        # Agrupar por estación
        def obtener_estacion(mes):
            if mes in [12, 1, 2]:
                return 'Verano'
            elif mes in [3, 4, 5]:
                return 'Otoño'
            elif mes in [6, 7, 8]:
                return 'Invierno'
            else:
                return 'Primavera'
        
        indice_diario['estacion'] = indice_diario['mes'].apply(obtener_estacion)
        
        analisis_estacional = indice_diario.groupby(['estacion', 'clasificacion']).size().unstack(fill_value=0)
        
        for estacion in ['Verano', 'Otoño', 'Invierno', 'Primavera']:
            if estacion in analisis_estacional.index:
                print(f"\n🌍 {estacion}:")
                total_estacion = analisis_estacional.loc[estacion].sum()
                for categoria in ['Despejado', 'Parcialmente nuboso', 'Muy nuboso']:
                    if categoria in analisis_estacional.columns:
                        cantidad = analisis_estacional.loc[estacion, categoria]
                        porcentaje = (cantidad / total_estacion) * 100
                        print(f"   {categoria}: {cantidad} días ({porcentaje:.1f}%)")
        
        print("=" * 60)
        
        return indice_diario

    def graficar_analisis_nubosidad(self, guardar_grafico=True):
        """
        Genera gráficos para el análisis de nubosidad
        """
        print("\n📊 GENERANDO GRÁFICOS DE ANÁLISIS DE NUBOSIDAD...")
        
        # Clasificar días si no se ha hecho
        if 'indice_claridad' not in self.datos.columns:
            indice_diario = self.clasificar_dias_nubosos()
        else:
            # Recalcular clasificación diaria
            datos_luz = self.datos[self.datos['ghi'] > 0].copy()
            indice_diario = datos_luz.groupby([datos_luz['mes'], datos_luz['dia']]).agg({
                'indice_claridad': 'mean',
                'ghi': ['mean', 'max'],
                'ghi_teorico': 'mean'
            }).round(3)
            indice_diario.columns = ['indice_claridad_prom', 'ghi_mean', 'ghi_max', 'ghi_teorico_mean']
            indice_diario = indice_diario.reset_index()
            
            def clasificar_dia(indice):
                if indice >= 0.7:
                    return 'Despejado'
                elif indice >= 0.4:
                    return 'Parcialmente nuboso'
                else:
                    return 'Muy nuboso'
            
            indice_diario['clasificacion'] = indice_diario['indice_claridad_prom'].apply(clasificar_dia)
            indice_diario['fecha'] = pd.to_datetime(
                indice_diario.apply(lambda x: f"2000-{x['mes']:02d}-{x['dia']:02d}", axis=1)
            )
        
        # Crear figura con múltiples subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        # Gráfico 1: Índice de claridad a lo largo del año
        colores = {'Despejado': 'gold', 'Parcialmente nuboso': 'orange', 'Muy nuboso': 'gray'}
        
        for categoria in ['Despejado', 'Parcialmente nuboso', 'Muy nuboso']:
            datos_cat = indice_diario[indice_diario['clasificacion'] == categoria]
            ax1.scatter(datos_cat['fecha'], datos_cat['indice_claridad_prom'], 
                       c=colores[categoria], label=categoria, alpha=0.7, s=30)
        
        ax1.axhline(y=0.7, color='red', linestyle='--', alpha=0.7, label='Umbral despejado')
        ax1.axhline(y=0.4, color='orange', linestyle='--', alpha=0.7, label='Umbral nuboso')
        ax1.set_title('Índice de Claridad Diario - TMY Antofagasta', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Índice de Claridad', fontsize=12)
        ax1.set_xlabel('Fecha', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        
        # Gráfico 2: Distribución de clasificaciones
        conteo_dias = indice_diario['clasificacion'].value_counts()
        colores_pie = [colores[cat] for cat in conteo_dias.index]
        
        wedges, texts, autotexts = ax2.pie(conteo_dias.values, labels=conteo_dias.index, 
                                          autopct='%1.1f%%', colors=colores_pie, startangle=90)
        ax2.set_title('Distribución de Días por Nubosidad', fontsize=14, fontweight='bold')
        
        # Gráfico 3: Comparación GHI observado vs teórico
        # Seleccionar algunos días representativos
        dias_muestra = indice_diario.sample(n=min(50, len(indice_diario)))
        
        ax3.scatter(dias_muestra['ghi_teorico_mean'], dias_muestra['ghi_mean'], 
                   c=[colores[cat] for cat in dias_muestra['clasificacion']], 
                   alpha=0.7, s=50)
        
        # Línea de referencia (GHI observado = GHI teórico)
        max_val = max(dias_muestra['ghi_teorico_mean'].max(), dias_muestra['ghi_mean'].max())
        ax3.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='GHI obs = GHI teórico')
        
        ax3.set_xlabel('GHI Teórico (W/m²)', fontsize=12)
        ax3.set_ylabel('GHI Observado (W/m²)', fontsize=12)
        ax3.set_title('GHI Observado vs Teórico', fontsize=14, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Gráfico 4: Análisis estacional
        def obtener_estacion(mes):
            if mes in [12, 1, 2]:
                return 'Verano'
            elif mes in [3, 4, 5]:
                return 'Otoño'
            elif mes in [6, 7, 8]:
                return 'Invierno'
            else:
                return 'Primavera'
        
        indice_diario['estacion'] = indice_diario['mes'].apply(obtener_estacion)
        
        # Crear tabla de contingencia
        tabla_estacional = pd.crosstab(indice_diario['estacion'], indice_diario['clasificacion'])
        
        # Convertir a porcentajes
        tabla_porcentajes = tabla_estacional.div(tabla_estacional.sum(axis=1), axis=0) * 100
        
        # Gráfico de barras apiladas
        tabla_porcentajes.plot(kind='bar', stacked=True, ax=ax4, 
                              color=[colores[cat] for cat in tabla_porcentajes.columns])
        ax4.set_title('Distribución Estacional de Nubosidad', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Porcentaje (%)', fontsize=12)
        ax4.set_xlabel('Estación', fontsize=12)
        ax4.legend(title='Clasificación', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'OFFGRID/results/nubosidad/analisis_nubosidad_tmy_antofagasta.png'
            plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
            print(f"💾 Gráfico guardado como: {nombre_archivo}")
        
        plt.show()
        
        return fig, indice_diario

    def analizar_dia_especifico_nubosidad(self, mes, dia):
        """
        Analiza en detalle la nubosidad de un día específico
        
        Args:
            mes (int): Mes (1-12)
            dia (int): Día del mes
        """
        print(f"\n🔍 ANÁLISIS DETALLADO DE NUBOSIDAD - {dia}/{mes}")
        print("=" * 60)
        
        # Asegurar que el índice de claridad esté calculado
        if 'indice_claridad' not in self.datos.columns:
            self.calcular_indice_claridad()
        
        # Filtrar datos del día específico
        datos_dia = self.datos[
            (self.datos['mes'] == mes) & (self.datos['dia'] == dia)
        ].copy()
        
        if len(datos_dia) == 0:
            print(f"❌ No se encontraron datos para {dia}/{mes}")
            return None
        
        # Filtrar solo horas de luz
        datos_luz = datos_dia[datos_dia['ghi'] > 0]
        
        if len(datos_luz) == 0:
            print(f"❌ No hay horas de luz para {dia}/{mes}")
            return None
        
        # Calcular estadísticas del día
        indice_promedio = datos_luz['indice_claridad'].mean()
        indice_std = datos_luz['indice_claridad'].std()
        ghi_max = datos_luz['ghi'].max()
        ghi_teorico_max = datos_luz['ghi_teorico'].max()
        horas_luz = len(datos_luz)
        
        # Clasificar el día
        if indice_promedio >= 0.7:
            clasificacion = 'Despejado'
        elif indice_promedio >= 0.4:
            clasificacion = 'Parcialmente nuboso'
        else:
            clasificacion = 'Muy nuboso'
        
        print(f"📊 ESTADÍSTICAS DEL DÍA:")
        print(f"   Clasificación: {clasificacion}")
        print(f"   Índice de claridad promedio: {indice_promedio:.3f}")
        print(f"   Desviación estándar del índice: {indice_std:.3f}")
        print(f"   GHI máximo observado: {ghi_max:.1f} W/m²")
        print(f"   GHI máximo teórico: {ghi_teorico_max:.1f} W/m²")
        print(f"   Eficiencia máxima: {(ghi_max/ghi_teorico_max)*100:.1f}%")
        print(f"   Horas de luz: {horas_luz}")
        
        
        # Análisis horario detallado
        print(f"\n⏰ ANÁLISIS HORARIO DETALLADO:")
        print("-" * 50)
        
        for _, hora_data in datos_luz.iterrows():
            hora = int(hora_data['hora'])
            indice = hora_data['indice_claridad']
            ghi_obs = hora_data['ghi']
            ghi_teo = hora_data['ghi_teorico']
            
            if indice < 0.4:
                estado = "☁️ Muy nuboso"
            elif indice < 0.7:
                estado = "⛅ Parcialmente nuboso"
            else:
                estado = "☀️ Despejado"
            
            print(f"   {hora:02d}:00 - {estado} (Índice: {indice:.3f}, "
                  f"GHI: {ghi_obs:.0f}/{ghi_teo:.0f} W/m²)")
        
        return {
            'clasificacion': clasificacion,
            'indice_promedio': indice_promedio,
            'indice_std': indice_std,
            'ghi_max': ghi_max,
            'ghi_teorico_max': ghi_teorico_max,
            'horas_luz': horas_luz,
            'datos_dia': datos_dia
        }

    def analizar_rachas_dias_nubosos(self):
        """
        Analiza las rachas consecutivas de días nubosos y encuentra la secuencia más larga
        
        Returns:
            dict: Información sobre las rachas de días nubosos
        """
        print("\n☁️📊 ANALIZANDO RACHAS DE DÍAS NUBOSOS CONSECUTIVOS...")
        print("=" * 70)
        
        # Asegurar que el índice de claridad esté calculado
        if 'indice_claridad' not in self.datos.columns:
            self.calcular_indice_claridad()
        
        # Obtener clasificación diaria
        datos_luz = self.datos[self.datos['ghi'] > 0].copy()
        
        indice_diario = datos_luz.groupby([datos_luz['mes'], datos_luz['dia']]).agg({
            'indice_claridad': 'mean',
            'ghi': 'mean'
        }).round(3)
        
        indice_diario.columns = ['indice_claridad_prom', 'ghi_mean']
        indice_diario = indice_diario.reset_index()
        
        # Clasificar días
        def clasificar_dia(indice):
            if indice >= 0.7:
                return 'Despejado'
            elif indice >= 0.4:
                return 'Parcialmente nuboso'
            else:
                return 'Muy nuboso'
        
        indice_diario['clasificacion'] = indice_diario['indice_claridad_prom'].apply(clasificar_dia)
        
        # Agregar fecha ordenada para análisis temporal
        indice_diario['fecha'] = pd.to_datetime(
            indice_diario.apply(lambda x: f"2000-{x['mes']:02d}-{x['dia']:02d}", axis=1)
        )
        indice_diario = indice_diario.sort_values('fecha').reset_index(drop=True)
        
        # Encontrar rachas consecutivas de cada tipo
        def encontrar_rachas(serie_clasificacion, tipo_dia):
            """Encuentra todas las rachas consecutivas de un tipo específico de día"""
            rachas = []
            racha_actual = []
            
            for i, clasificacion in enumerate(serie_clasificacion):
                if clasificacion == tipo_dia:
                    racha_actual.append(i)
                else:
                    if len(racha_actual) > 0:
                        rachas.append(racha_actual.copy())
                        racha_actual = []
            
            # Agregar la última racha si existe
            if len(racha_actual) > 0:
                rachas.append(racha_actual)
            
            return rachas
        
        # Encontrar rachas para cada tipo de día
        rachas_muy_nuboso = encontrar_rachas(indice_diario['clasificacion'], 'Muy nuboso')
        rachas_parcialmente_nuboso = encontrar_rachas(indice_diario['clasificacion'], 'Parcialmente nuboso')
        rachas_despejado = encontrar_rachas(indice_diario['clasificacion'], 'Despejado')
        
        # Encontrar la racha más larga de días muy nubosos
        if rachas_muy_nuboso:
            racha_mas_larga_muy_nuboso = max(rachas_muy_nuboso, key=len)
            dias_consecutivos_max = len(racha_mas_larga_muy_nuboso)
            
            # Obtener información detallada de la racha más larga
            inicio_racha = racha_mas_larga_muy_nuboso[0]
            fin_racha = racha_mas_larga_muy_nuboso[-1]
            
            fecha_inicio = indice_diario.loc[inicio_racha, 'fecha']
            fecha_fin = indice_diario.loc[fin_racha, 'fecha']
            
            print(f"☁️ RACHA MÁS LARGA DE DÍAS MUY NUBOSOS:")
            print(f"   Duración: {dias_consecutivos_max} días consecutivos")
            print(f"   Período: {fecha_inicio.strftime('%d/%m')} - {fecha_fin.strftime('%d/%m')}")
            print(f"   Índices de claridad promedio durante la racha:")
            
            for i, idx in enumerate(racha_mas_larga_muy_nuboso):
                dia_info = indice_diario.loc[idx]
                print(f"     Día {i+1}: {dia_info['fecha'].strftime('%d/%m')} - "
                      f"Índice: {dia_info['indice_claridad_prom']:.3f} - "
                      f"GHI: {dia_info['ghi_mean']:.1f} W/m²")
        else:
            dias_consecutivos_max = 0
            fecha_inicio = None
            fecha_fin = None
            print("☁️ No se encontraron días muy nubosos en el TMY")
        
        # Estadísticas de todas las rachas de días muy nubosos
        if rachas_muy_nuboso:
            longitudes_rachas = [len(racha) for racha in rachas_muy_nuboso]
            
            print(f"\n📊 ESTADÍSTICAS DE RACHAS DE DÍAS MUY NUBOSOS:")
            print(f"   Total de rachas: {len(rachas_muy_nuboso)}")
            print(f"   Racha más larga: {max(longitudes_rachas)} días")
            print(f"   Racha más corta: {min(longitudes_rachas)} días")
            print(f"   Promedio de duración: {np.mean(longitudes_rachas):.1f} días")
            print(f"   Mediana de duración: {np.median(longitudes_rachas):.1f} días")
            
            # Distribución de longitudes
            print(f"\n📈 DISTRIBUCIÓN DE LONGITUDES DE RACHAS:")
            from collections import Counter
            contador_longitudes = Counter(longitudes_rachas)
            for longitud in sorted(contador_longitudes.keys()):
                cantidad = contador_longitudes[longitud]
                print(f"   {longitud} día(s): {cantidad} rachas")
        
        # Análisis de rachas de días parcialmente nubosos
        if rachas_parcialmente_nuboso:
            longitudes_parcial = [len(racha) for racha in rachas_parcialmente_nuboso]
            racha_mas_larga_parcial = max(rachas_parcialmente_nuboso, key=len)
            
            print(f"\n⛅ RACHA MÁS LARGA DE DÍAS PARCIALMENTE NUBOSOS:")
            print(f"   Duración: {len(racha_mas_larga_parcial)} días consecutivos")
            print(f"   Total de rachas: {len(rachas_parcialmente_nuboso)}")
            print(f"   Promedio de duración: {np.mean(longitudes_parcial):.1f} días")
        
        # Análisis de rachas de días despejados
        if rachas_despejado:
            longitudes_despejado = [len(racha) for racha in rachas_despejado]
            racha_mas_larga_despejado = max(rachas_despejado, key=len)
            
            inicio_despejado = racha_mas_larga_despejado[0]
            fin_despejado = racha_mas_larga_despejado[-1]
            fecha_inicio_despejado = indice_diario.loc[inicio_despejado, 'fecha']
            fecha_fin_despejado = indice_diario.loc[fin_despejado, 'fecha']
            
            print(f"\n☀️ RACHA MÁS LARGA DE DÍAS DESPEJADOS:")
            print(f"   Duración: {len(racha_mas_larga_despejado)} días consecutivos")
            print(f"   Período: {fecha_inicio_despejado.strftime('%d/%m')} - {fecha_fin_despejado.strftime('%d/%m')}")
            print(f"   Total de rachas: {len(rachas_despejado)}")
            print(f"   Promedio de duración: {np.mean(longitudes_despejado):.1f} días")
        
        # Análisis estacional de rachas
        print(f"\n🌍 ANÁLISIS ESTACIONAL DE RACHAS MUY NUBOSAS:")
        print("-" * 50)
        
        def obtener_estacion(fecha):
            mes = fecha.month
            if mes in [12, 1, 2]:
                return 'Verano'
            elif mes in [3, 4, 5]:
                return 'Otoño'
            elif mes in [6, 7, 8]:
                return 'Invierno'
            else:
                return 'Primavera'
        
        rachas_por_estacion = {'Verano': [], 'Otoño': [], 'Invierno': [], 'Primavera': []}
        
        for racha in rachas_muy_nuboso:
            fecha_inicio_racha = indice_diario.loc[racha[0], 'fecha']
            estacion = obtener_estacion(fecha_inicio_racha)
            rachas_por_estacion[estacion].append(len(racha))
        
        for estacion, longitudes in rachas_por_estacion.items():
            if longitudes:
                print(f"   {estacion}: {len(longitudes)} rachas, "
                      f"máxima {max(longitudes)} días, "
                      f"promedio {np.mean(longitudes):.1f} días")
            else:
                print(f"   {estacion}: 0 rachas")
        
        # Implicaciones para sistemas fotovoltaicos
        print(f"\n⚡ IMPLICACIONES PARA SISTEMAS FOTOVOLTAICOS:")
        print("=" * 60)
        
        if dias_consecutivos_max > 0:
            print(f"🔋 AUTONOMÍA REQUERIDA:")
            print(f"   Días consecutivos máximos sin sol pleno: {dias_consecutivos_max}")
            print(f"   Recomendación: Diseñar sistema con autonomía de al menos {dias_consecutivos_max + 1} días")
            
            # Calcular reducción de energía durante la racha más larga
            if rachas_muy_nuboso:
                energia_reducida = []
                for idx in racha_mas_larga_muy_nuboso:
                    dia_info = indice_diario.loc[idx]
                    # Estimar energía perdida comparado con un día despejado típico
                    ghi_despejado_tipico = 500  # W/m² promedio estimado para día despejado
                    reduccion = (1 - dia_info['indice_claridad_prom']) * 100
                    energia_reducida.append(reduccion)
                
                reduccion_promedio = np.mean(energia_reducida)
                print(f"   Reducción promedio de energía durante la racha: {reduccion_promedio:.1f}%")
                print(f"   Energía disponible promedio durante la racha: {100 - reduccion_promedio:.1f}%")
        else:
            print("✅ No hay días muy nubosos consecutivos en el TMY")
        
        print("=" * 70)
        
        # Preparar datos de retorno
        resultado = {
            'dias_consecutivos_max': dias_consecutivos_max,
            'fecha_inicio_racha_max': fecha_inicio,
            'fecha_fin_racha_max': fecha_fin,
            'total_rachas_muy_nuboso': len(rachas_muy_nuboso) if rachas_muy_nuboso else 0,
            'rachas_muy_nuboso': rachas_muy_nuboso,
            'rachas_parcialmente_nuboso': rachas_parcialmente_nuboso,
            'rachas_despejado': rachas_despejado,
            'datos_clasificacion': indice_diario
        }
        
        return resultado

    def graficar_rachas_nubosidad(self, datos_rachas, guardar_grafico=True):
        """
        Genera gráficos para visualizar las rachas de días nubosos
        
        Args:
            datos_rachas: Resultado de analizar_rachas_dias_nubosos()
            guardar_grafico: Si guardar el gráfico
        """
        print("\n📊 GENERANDO GRÁFICOS DE RACHAS DE NUBOSIDAD...")
        
        # Crear figura con múltiples subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        # Datos de clasificación
        indice_diario = datos_rachas['datos_clasificacion']
        
        # Gráfico 1: Timeline de clasificación de días
        colores = {'Despejado': 'gold', 'Parcialmente nuboso': 'orange', 'Muy nuboso': 'gray'}
        
        for i, (_, dia) in enumerate(indice_diario.iterrows()):
            color = colores[dia['clasificacion']]
            ax1.bar(dia['fecha'], 1, color=color, alpha=0.7, width=1)
        
        ax1.set_title('Clasificación Diaria de Nubosidad - Año TMY', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Clasificación', fontsize=12)
        ax1.set_xlabel('Fecha', fontsize=12)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        
        # Crear leyenda personalizada
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=colores[cat], label=cat) for cat in colores.keys()]
        ax1.legend(handles=legend_elements, loc='upper right')
        
        # Gráfico 2: Distribución de longitudes de rachas muy nubosas
        if datos_rachas['rachas_muy_nuboso']:
            longitudes = [len(racha) for racha in datos_rachas['rachas_muy_nuboso']]
            from collections import Counter
            contador = Counter(longitudes)
            
            longitudes_unicas = sorted(contador.keys())
            frecuencias = [contador[l] for l in longitudes_unicas]
            
            ax2.bar(longitudes_unicas, frecuencias, color='gray', alpha=0.7)
            ax2.set_title('Distribución de Longitudes de Rachas\nMuy Nubosas', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Días consecutivos', fontsize=12)
            ax2.set_ylabel('Número de rachas', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Marcar la racha más larga
            max_longitud = max(longitudes)
            ax2.axvline(x=max_longitud, color='red', linestyle='--', linewidth=2, 
                       label=f'Racha más larga: {max_longitud} días')
            ax2.legend()
        else:
            ax2.text(0.5, 0.5, 'No hay rachas de días\nmuy nubosos', 
                    ha='center', va='center', transform=ax2.transAxes, fontsize=14)
            ax2.set_title('Distribución de Longitudes de Rachas\nMuy Nubosas', fontsize=14, fontweight='bold')
        
        # Gráfico 3: Comparación de rachas por tipo
        tipos_rachas = ['Muy nuboso', 'Parcialmente nuboso', 'Despejado']
        datos_rachas_tipos = [
            datos_rachas['rachas_muy_nuboso'],
            datos_rachas['rachas_parcialmente_nuboso'],
            datos_rachas['rachas_despejado']
        ]
        
        max_longitudes = []
        promedios = []
        totales = []
        
        for rachas in datos_rachas_tipos:
            if rachas:
                longitudes = [len(racha) for racha in rachas]
                max_longitudes.append(max(longitudes))
                promedios.append(np.mean(longitudes))
                totales.append(len(rachas))
            else:
                max_longitudes.append(0)
                promedios.append(0)
                totales.append(0)
        
        x = np.arange(len(tipos_rachas))
        width = 0.25
        
        ax3.bar(x - width, max_longitudes, width, label='Racha más larga', 
               color=['gray', 'orange', 'gold'], alpha=0.7)
        ax3.bar(x, promedios, width, label='Promedio', 
               color=['gray', 'orange', 'gold'], alpha=0.5)
        ax3.bar(x + width, totales, width, label='Total de rachas', 
               color=['gray', 'orange', 'gold'], alpha=0.3)
        
        ax3.set_title('Comparación de Rachas por Tipo de Día', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Días / Cantidad', fontsize=12)
        ax3.set_xlabel('Tipo de día', fontsize=12)
        ax3.set_xticks(x)
        ax3.set_xticklabels(tipos_rachas)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Gráfico 4: Análisis estacional de rachas muy nubosas
        def obtener_estacion(fecha):
            mes = fecha.month
            if mes in [12, 1, 2]:
                return 'Verano'
            elif mes in [3, 4, 5]:
                return 'Otoño'
            elif mes in [6, 7, 8]:
                return 'Invierno'
            else:
                return 'Primavera'
        
        rachas_por_estacion = {'Verano': [], 'Otoño': [], 'Invierno': [], 'Primavera': []}
        
        for racha in datos_rachas['rachas_muy_nuboso']:
            fecha_inicio = indice_diario.loc[racha[0], 'fecha']
            estacion = obtener_estacion(fecha_inicio)
            rachas_por_estacion[estacion].append(len(racha))
        
        estaciones = list(rachas_por_estacion.keys())
        cantidades = [len(rachas_por_estacion[est]) for est in estaciones]
        max_por_estacion = [max(rachas_por_estacion[est]) if rachas_por_estacion[est] else 0 for est in estaciones]
        
        x_est = np.arange(len(estaciones))
        width_est = 0.35
        
        ax4.bar(x_est - width_est/2, cantidades, width_est, label='Cantidad de rachas', 
               color='lightblue', alpha=0.7)
        ax4.bar(x_est + width_est/2, max_por_estacion, width_est, label='Racha más larga', 
               color='darkblue', alpha=0.7)
        
        ax4.set_title('Rachas Muy Nubosas por Estación', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Días / Cantidad', fontsize=12)
        ax4.set_xlabel('Estación', fontsize=12)
        ax4.set_xticks(x_est)
        ax4.set_xticklabels(estaciones)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'OFFGRID/results/rachas_nubosidad_tmy_antofagasta.png'
            plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
            print(f"💾 Gráfico guardado como: {nombre_archivo}")
        
        plt.show()
        
        return fig

def main():
    """Función principal"""
    print("🚀 PROCESADOR TMY ANTOFAGASTA")
    print("=" * 50)
    
    # Inicializar procesador
    procesador = ProcesadorTMY('/home/nicole/UA/OFFGRID/OFFGRID/data/DHTMY_E_17WEZY.csv')
    
    # Escanear archivo
    info_archivo = procesador.scanner_archivo()
    
    # Cargar y procesar datos
    datos = procesador.cargar_datos()
    datos_procesados = procesador.procesar_datos()
    
    # Calcular temperaturas durante horas de luz
    stats_temp_luz = procesador.calcular_temperaturas_horas_luz()
    
    # Calcular GHI diario de los solsticios
    stats_ghi_solsticios = procesador.calcular_ghi_diario_solsticios()
    
    # NUEVO: Análisis de nubosidad
    print("\n🌤️ INICIANDO ANÁLISIS DE NUBOSIDAD...")
    
    # Calcular índice de claridad para todos los datos
    procesador.calcular_indice_claridad()
    
    # Clasificar días según nubosidad
    clasificacion_dias = procesador.clasificar_dias_nubosos()
    
    # Generar gráficos de nubosidad
    procesador.graficar_analisis_nubosidad()
    
    # Analizar días específicos como ejemplo
    print("\n🔍 ANALIZANDO DÍAS ESPECÍFICOS...")
    
    # Ejemplo: Analizar el solsticio de invierno (20 de junio)
    procesador.analizar_dia_especifico_nubosidad(6, 20)
    
    # Ejemplo: Analizar el solsticio de verano (21 de diciembre)
    procesador.analizar_dia_especifico_nubosidad(12, 21)
    
    # Encontrar y analizar el día más nuboso del año
    dia_mas_nuboso = clasificacion_dias.loc[clasificacion_dias['indice_claridad_prom'].idxmin()]
    print(f"\n☁️ ANALIZANDO EL DÍA MÁS NUBOSO DEL AÑO:")
    print(f"   Fecha: {dia_mas_nuboso['fecha'].strftime('%d/%m')}")
    print(f"   Índice de claridad: {dia_mas_nuboso['indice_claridad_prom']:.3f}")
    procesador.analizar_dia_especifico_nubosidad(dia_mas_nuboso['mes'], dia_mas_nuboso['dia'])
    
    # Encontrar y analizar el día más despejado del año
    dia_mas_despejado = clasificacion_dias.loc[clasificacion_dias['indice_claridad_prom'].idxmax()]
    print(f"\n☀️ ANALIZANDO EL DÍA MÁS DESPEJADO DEL AÑO:")
    print(f"   Fecha: {dia_mas_despejado['fecha'].strftime('%d/%m')}")
    print(f"   Índice de claridad: {dia_mas_despejado['indice_claridad_prom']:.3f}")
    procesador.analizar_dia_especifico_nubosidad(dia_mas_despejado['mes'], dia_mas_despejado['dia'])
    
    # Generar gráficos originales
    print("\n🎨 GENERANDO GRÁFICOS ORIGINALES...")
    procesador.graficar_radiacion_anual()
    procesador.graficar_comparacion_mensual()
    procesador.graficar_solsticios()
    
    # Exportar días seleccionados a Excel
    print("\n📊 EXPORTANDO DATOS A EXCEL...")
    
    # Exportar días por defecto (solsticios)
    archivo_excel = procesador.exportar_dias_a_excel()
    
    # Exportar días con diferentes niveles de nubosidad
    dias_nubosidad = [
        (dia_mas_despejado['mes'], dia_mas_despejado['dia']),  # Día más despejado
        (dia_mas_nuboso['mes'], dia_mas_nuboso['dia']),       # Día más nuboso
        (6, 20),  # Solsticio de invierno
        (12, 21)  # Solsticio de verano
    ]
    
    archivo_excel_nubosidad = procesador.exportar_dias_a_excel(
        dias_seleccionados=dias_nubosidad,
        nombre_archivo='OFFGRID/data/Analisis_nubosidad_dias_representativos.xlsx'
    )
    
    # Generar reporte
    reporte = procesador.generar_reporte()
    
    # Generar reporte adicional de nubosidad
    print("\n📋 REPORTE DE NUBOSIDAD:")
    print("=" * 50)
    conteo_dias = clasificacion_dias['clasificacion'].value_counts()
    total_dias = len(clasificacion_dias)
    
    print(f"📊 RESUMEN ANUAL DE NUBOSIDAD:")
    for categoria, cantidad in conteo_dias.items():
        porcentaje = (cantidad / total_dias) * 100
        print(f"   {categoria}: {cantidad} días ({porcentaje:.1f}%)")
    
    print(f"\n📈 ESTADÍSTICAS DE ÍNDICE DE CLARIDAD:")
    print(f"   Promedio anual: {clasificacion_dias['indice_claridad_prom'].mean():.3f}")
    print(f"   Máximo: {clasificacion_dias['indice_claridad_prom'].max():.3f}")
    print(f"   Mínimo: {clasificacion_dias['indice_claridad_prom'].min():.3f}")
    print(f"   Desviación estándar: {clasificacion_dias['indice_claridad_prom'].std():.3f}")
    
    print("\n✅ PROCESAMIENTO COMPLETADO!")
    print("📁 Los gráficos y archivos Excel han sido guardados en los directorios correspondientes.")
    print("🌤️ Se ha incluido el análisis completo de nubosidad con clasificación de días.")
    print(reporte)

# Función auxiliar para análisis rápido de un día específico
def analizar_dia_rapido(mes, dia):
    """
    Función auxiliar para análisis rápido de nubosidad de un día específico
    
    Args:
        mes (int): Mes (1-12)
        dia (int): Día del mes
    """
    print(f"🔍 ANÁLISIS RÁPIDO DE NUBOSIDAD - {dia}/{mes}")
    
    # Inicializar procesador
    procesador = ProcesadorTMY('/home/nicole/UA/OFFGRID/OFFGRID/data/DHTMY_E_17WEZY.csv')
    
    # Cargar datos mínimos necesarios
    datos = procesador.cargar_datos()
    datos_procesados = procesador.procesar_datos()
    
    # Analizar día específico
    resultado = procesador.analizar_dia_especifico_nubosidad(mes, dia)
    
    return resultado

# Ejemplo de uso:
# Para analizar un día específico rápidamente, usar:
# resultado = analizar_dia_rapido(6, 20)  # Analizar 20 de junio

if __name__ == "__main__":
    main() 