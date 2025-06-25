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
        
        # Calcular Gmod inclinado a 20°
        print("🔧 Calculando Gmod inclinado a 20°...")
        self.datos['gmod_20'] = self.calcular_gmod_inclinado(
            self.datos['ghi'].values, 
            self.datos['fecha_tmy'].values, 
            latitud=-23.14, 
            beta=20
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
        datos_faltantes = self.datos[['ghi', 'glb']].isnull().sum()
        print(f"📊 Datos faltantes:")
        print(f"   GHI: {datos_faltantes['ghi']}")
        print(f"   GLB: {datos_faltantes['glb']}")
        
        # Estadísticas básicas
        print(f"\n📈 ESTADÍSTICAS BÁSICAS:")
        print(f"   GHI - Máximo: {self.datos['ghi'].max():.1f} W/m²")
        print(f"   GHI - Promedio: {self.datos['ghi'].mean():.1f} W/m²")
        print(f"   GLB - Máximo: {self.datos['glb'].max():.1f} W/m²")
        print(f"   GLB - Promedio: {self.datos['glb'].mean():.1f} W/m²")
        
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
        
        # Gráfico 2: Radiación Gmod inclinado a 20°
        ax2.plot(self.datos['fecha_tmy'], self.datos['gmod_20'], 
                color='blue', linewidth=0.8, alpha=0.7, label='Gmod (Inclinado 20°)')
        ax2.set_title('Radiación Solar Gmod Inclinado a 20° - TMY Antofagasta', 
                     fontsize=16, fontweight='bold')
        ax2.set_ylabel('Radiación (W/m²)', fontsize=12)
        ax2.set_xlabel('Mes', fontsize=12)
        ax2.legend(fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'radiacion_solar_tmy_antofagasta.png'
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
            'gmod_20': ['mean', 'max']
        }).round(2)
        
        # Aplanar columnas
        datos_mensuales.columns = ['ghi_mean', 'ghi_max', 'gmod_20_mean', 'gmod_20_max']
        datos_mensuales = datos_mensuales.reset_index()
        
        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Configurar posiciones de barras
        x = np.arange(len(datos_mensuales))
        width = 0.35
        
        # Gráfico 1: Promedios mensuales
        ax1.bar(x - width/2, datos_mensuales['ghi_mean'], width, 
               label='GHI (Global Horizontal)', color='orange', alpha=0.7)
        ax1.bar(x + width/2, datos_mensuales['gmod_20_mean'], width, 
               label='Gmod (Inclinado 20°)', color='blue', alpha=0.7)
        
        ax1.set_xlabel('Mes', fontsize=12)
        ax1.set_ylabel('Radiación Promedio (W/m²)', fontsize=12)
        ax1.set_title('Radiación Solar Promedio Mensual - TMY Antofagasta', 
                     fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'])
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Máximos mensuales
        ax2.bar(x - width/2, datos_mensuales['ghi_max'], width, 
               label='GHI (Global Horizontal)', color='orange', alpha=0.7)
        ax2.bar(x + width/2, datos_mensuales['gmod_20_max'], width, 
               label='Gmod (Inclinado 20°)', color='blue', alpha=0.7)
        
        ax2.set_xlabel('Mes', fontsize=12)
        ax2.set_ylabel('Radiación Máxima (W/m²)', fontsize=12)
        ax2.set_title('Radiación Solar Máxima Mensual - TMY Antofagasta', 
                     fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'])
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'comparacion_mensual_tmy_antofagasta.png'
            plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
            print(f"💾 Gráfico guardado como: {nombre_archivo}")
        
        plt.show()
        
        return fig, datos_mensuales
    
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
        ax1.plot(horas_verano, solsticio_verano['gmod_20'], 
                color='blue', linewidth=2, marker='^', markersize=4, 
                label='Gmod (Inclinado 20°)', alpha=0.8)
        
        # Encontrar y marcar máximos para verano
        ghi_max_idx_verano = solsticio_verano['ghi'].idxmax()
        gmod_max_idx_verano = solsticio_verano['gmod_20'].idxmax()
        
        ghi_max_hora_verano = solsticio_verano.loc[ghi_max_idx_verano, 'hora']
        ghi_max_valor_verano = solsticio_verano.loc[ghi_max_idx_verano, 'ghi']
        gmod_max_hora_verano = solsticio_verano.loc[gmod_max_idx_verano, 'hora']
        gmod_max_valor_verano = solsticio_verano.loc[gmod_max_idx_verano, 'gmod_20']
        
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
        gmod_max_verano = solsticio_verano['gmod_20'].max()
        ghi_energia_verano = solsticio_verano['ghi'].sum() * 3600 / 1e6  # kWh/m²
        gmod_energia_verano = solsticio_verano['gmod_20'].sum() * 3600 / 1e6  # kWh/m²
        
        ax1.text(0.02, 0.98, f'GHI máx: {ghi_max_verano:.0f} W/m²\nGmod máx: {gmod_max_verano:.0f} W/m²\nEnergía GHI: {ghi_energia_verano:.2f} kWh/m²\nEnergía Gmod: {gmod_energia_verano:.2f} kWh/m²', 
                transform=ax1.transAxes, verticalalignment='top', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Gráfico 2: Solsticio de Invierno (21 de Diciembre)
        horas_invierno = solsticio_invierno['hora']
        ax2.plot(horas_invierno, solsticio_invierno['ghi'], 
                color='orange', linewidth=2, marker='o', markersize=4, 
                label='GHI (Global Horizontal)', alpha=0.8)
        ax2.plot(horas_invierno, solsticio_invierno['gmod_20'], 
                color='blue', linewidth=2, marker='^', markersize=4, 
                label='Gmod (Inclinado 20°)', alpha=0.8)
        
        # Encontrar y marcar máximos para invierno
        ghi_max_idx_invierno = solsticio_invierno['ghi'].idxmax()
        gmod_max_idx_invierno = solsticio_invierno['gmod_20'].idxmax()
        
        ghi_max_hora_invierno = solsticio_invierno.loc[ghi_max_idx_invierno, 'hora']
        ghi_max_valor_invierno = solsticio_invierno.loc[ghi_max_idx_invierno, 'ghi']
        gmod_max_hora_invierno = solsticio_invierno.loc[gmod_max_idx_invierno, 'hora']
        gmod_max_valor_invierno = solsticio_invierno.loc[gmod_max_idx_invierno, 'gmod_20']
        
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
        gmod_max_invierno = solsticio_invierno['gmod_20'].max()
        ghi_energia_invierno = solsticio_invierno['ghi'].sum() * 3600 / 1e6  # kWh/m²
        gmod_energia_invierno = solsticio_invierno['gmod_20'].sum() * 3600 / 1e6  # kWh/m²
        
        ax2.text(0.02, 0.98, f'GHI máx: {ghi_max_invierno:.0f} W/m²\nGmod máx: {gmod_max_invierno:.0f} W/m²\nEnergía GHI: {ghi_energia_invierno:.2f} kWh/m²\nEnergía Gmod: {gmod_energia_invierno:.2f} kWh/m²', 
                transform=ax2.transAxes, verticalalignment='top', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'solsticios_tmy_antofagasta.png'
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
            'media': self.datos['gmod_20'].mean(),
            'max': self.datos['gmod_20'].max(),
            'min': self.datos['gmod_20'].min(),
            'std': self.datos['gmod_20'].std()
        }
        
        # Calcular energía anual (kWh/m²)
        energia_ghi_anual = (self.datos['ghi'].sum() * 1) / 1000  # 1 hora por registro
        energia_gmod_anual = (self.datos['gmod_20'].sum() * 1) / 1000  # 1 hora por registro
        
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
        
        ESTADÍSTICAS GMOD (Inclinado 20°):
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

    def calcular_gmod_inclinado(self, ghi_data, fechas, latitud=-23.14, beta=20):
        """
        Calcula Gmod inclinado usando la fórmula del notebook
        Gmod = GHI * (sin(α + β) / sin(α))
        donde α es la altura solar y β es el ángulo de inclinación
        """
        # Convertir fechas numpy a datetime y calcular día del año
        if isinstance(fechas[0], np.datetime64):
            # Convertir numpy.datetime64 a datetime
            fechas_dt = pd.to_datetime(fechas)
            dias_año = np.array([fecha.timetuple().tm_yday for fecha in fechas_dt])
        else:
            dias_año = np.array([fecha.timetuple().tm_yday for fecha in fechas])
        
        # Calcular ángulo de declinación solar
        declinacion = 23.45 * np.sin(np.deg2rad((284 + dias_año) * 360 / 365))
        
        # Calcular altura solar α
        altura_solar = 90 + latitud - declinacion
        
        # Calcular Gmod usando la fórmula
        gmod = ghi_data * (np.sin(np.deg2rad(altura_solar + beta)) / np.sin(np.deg2rad(altura_solar)))
        
        # Manejar casos donde sin(α) = 0 (cuando el sol está en el horizonte)
        # En estos casos, Gmod = 0
        gmod = np.where(np.sin(np.deg2rad(altura_solar)) == 0, 0, gmod)
        
        # Asegurar que Gmod no sea negativo
        gmod = np.maximum(gmod, 0)
        
        return gmod

def main():
    """Función principal"""
    print("🚀 PROCESADOR TMY ANTOFAGASTA")
    print("=" * 50)
    
    # Inicializar procesador
    procesador = ProcesadorTMY('DHTMY_E_17WEZY.csv')
    
    # Escanear archivo
    info_archivo = procesador.scanner_archivo()
    
    # Cargar y procesar datos
    datos = procesador.cargar_datos()
    datos_procesados = procesador.procesar_datos()
    
    # Generar gráficos
    print("\n🎨 GENERANDO GRÁFICOS...")
    procesador.graficar_radiacion_anual()
    procesador.graficar_comparacion_mensual()
    procesador.graficar_solsticios()
    
    # Generar reporte
    reporte = procesador.generar_reporte()
    
    print("\n✅ PROCESAMIENTO COMPLETADO!")
    print("📁 Los gráficos han sido guardados en el directorio actual.")
    print(reporte)

if __name__ == "__main__":
    main() 