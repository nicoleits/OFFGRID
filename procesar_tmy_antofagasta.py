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
        
        print(f"✅ Datos cargados exitosamente")
        print(f"   Registros: {len(self.datos)}")
        print(f"   Columnas: {len(self.datos.columns)}")
        
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
        """Graficar radiación GHI y GLB para un año completo"""
        print("\n📊 GENERANDO GRÁFICO ANUAL...")
        
        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Gráfico 1: Radiación GHI (Horizontal)
        ax1.plot(self.datos['fecha_tmy'], self.datos['ghi'], 
                color='orange', linewidth=0.8, alpha=0.7, label='GHI (Horizontal)')
        ax1.set_title('Radiación Solar Global Horizontal (GHI) - TMY Antofagasta', 
                     fontsize=16, fontweight='bold')
        ax1.set_ylabel('Radiación (W/m²)', fontsize=12)
        ax1.set_xlabel('Fecha', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Configurar formato de fechas
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        
        # Gráfico 2: Radiación GLB (Inclinada)
        ax2.plot(self.datos['fecha_tmy'], self.datos['glb'], 
                color='red', linewidth=0.8, alpha=0.7, label='GLB (Inclinada)')
        ax2.set_title('Radiación Solar Global Inclinada (GLB) - TMY Antofagasta', 
                     fontsize=16, fontweight='bold')
        ax2.set_ylabel('Radiación (W/m²)', fontsize=12)
        ax2.set_xlabel('Fecha', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Configurar formato de fechas
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
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
        
        # Calcular promedios mensuales
        datos_mensuales = self.datos.groupby('mes').agg({
            'ghi': ['mean', 'max', 'min'],
            'glb': ['mean', 'max', 'min']
        }).round(1)
        
        # Flatten column names
        datos_mensuales.columns = ['_'.join(col).strip() for col in datos_mensuales.columns]
        datos_mensuales = datos_mensuales.reset_index()
        
        # Crear gráfico
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Gráfico 1: Promedios mensuales
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        x = np.arange(len(meses))
        width = 0.35
        
        ax1.bar(x - width/2, datos_mensuales['ghi_mean'], width, 
               label='GHI (Horizontal)', color='orange', alpha=0.7)
        ax1.bar(x + width/2, datos_mensuales['glb_mean'], width, 
               label='GLB (Inclinada)', color='red', alpha=0.7)
        
        ax1.set_xlabel('Mes', fontsize=12)
        ax1.set_ylabel('Radiación Promedio (W/m²)', fontsize=12)
        ax1.set_title('Radiación Solar Promedio Mensual - TMY Antofagasta', 
                     fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(meses)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Máximos mensuales
        ax2.bar(x - width/2, datos_mensuales['ghi_max'], width, 
               label='GHI (Horizontal)', color='orange', alpha=0.7)
        ax2.bar(x + width/2, datos_mensuales['glb_max'], width, 
               label='GLB (Inclinada)', color='red', alpha=0.7)
        
        ax2.set_xlabel('Mes', fontsize=12)
        ax2.set_ylabel('Radiación Máxima (W/m²)', fontsize=12)
        ax2.set_title('Radiación Solar Máxima Mensual - TMY Antofagasta', 
                     fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(meses)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if guardar_grafico:
            nombre_archivo = 'comparacion_mensual_tmy_antofagasta.png'
            plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
            print(f"💾 Gráfico guardado como: {nombre_archivo}")
        
        plt.show()
        
        return fig, datos_mensuales
    
    def generar_reporte(self):
        """Generar un reporte completo de los datos"""
        print("\n📋 GENERANDO REPORTE...")
        
        # Calcular estadísticas
        stats_ghi = self.datos['ghi'].describe()
        stats_glb = self.datos['glb'].describe()
        
        # Calcular energía diaria promedio
        energia_ghi_diaria = self.datos.groupby('dia_año')['ghi'].sum() * 3600 / 1e6  # kWh/m²
        energia_glb_diaria = self.datos.groupby('dia_año')['glb'].sum() * 3600 / 1e6  # kWh/m²
        
        # Calcular energía anual
        energia_ghi_anual = energia_ghi_diaria.sum()
        energia_glb_anual = energia_glb_diaria.sum()
        
        print("\n" + "="*60)
        print("📊 REPORTE TMY ANTOFAGASTA")
        print("="*60)
        print(f"📍 Ubicación: Antofagasta, Chile")
        print(f"   Latitud: {self.metadatos.get('LATITUD', 'N/A')}")
        print(f"   Longitud: {self.metadatos.get('LONGITUD', 'N/A')}")
        print(f"   Altura: {self.metadatos.get('ALTURA', 'N/A')} m")
        
        print(f"\n📅 Período de datos: {self.metadatos.get('FECHA INICIAL', 'N/A')} - {self.metadatos.get('FECHA FINAL', 'N/A')}")
        print(f"📊 Total de registros: {len(self.datos):,}")
        
        print(f"\n☀️ RADIACIÓN GHI (HORIZONTAL):")
        print(f"   Máximo: {stats_ghi['max']:.1f} W/m²")
        print(f"   Promedio: {stats_ghi['mean']:.1f} W/m²")
        print(f"   Mínimo: {stats_ghi['min']:.1f} W/m²")
        print(f"   Energía anual: {energia_ghi_anual:.1f} kWh/m²")
        
        print(f"\n☀️ RADIACIÓN GLB (INCLINADA):")
        print(f"   Máximo: {stats_glb['max']:.1f} W/m²")
        print(f"   Promedio: {stats_glb['mean']:.1f} W/m²")
        print(f"   Mínimo: {stats_glb['min']:.1f} W/m²")
        print(f"   Energía anual: {energia_glb_anual:.1f} kWh/m²")
        
        print(f"\n📈 COMPARACIÓN:")
        print(f"   Diferencia promedio: {stats_glb['mean'] - stats_ghi['mean']:.1f} W/m²")
        print(f"   Factor de mejora: {stats_glb['mean'] / stats_ghi['mean']:.2f}x")
        print(f"   Energía adicional: {energia_glb_anual - energia_ghi_anual:.1f} kWh/m²/año")
        
        return {
            'stats_ghi': stats_ghi,
            'stats_glb': stats_glb,
            'energia_ghi_anual': energia_ghi_anual,
            'energia_glb_anual': energia_glb_anual
        }

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
    
    # Generar reporte
    reporte = procesador.generar_reporte()
    
    print("\n✅ PROCESAMIENTO COMPLETADO!")
    print("📁 Los gráficos han sido guardados en el directorio actual.")

if __name__ == "__main__":
    main() 