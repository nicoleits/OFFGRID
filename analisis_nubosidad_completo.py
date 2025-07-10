#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS COMPLETO DE NUBOSIDAD - TMY ANTOFAGASTA
Código unificado para todos los análisis de días nubosos

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
import os
from collections import Counter
from matplotlib.patches import Patch

warnings.filterwarnings('ignore')

# Configurar estilo de gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class AnalizadorNubosidad:
    """Clase para análisis completo de nubosidad en datos TMY"""
    
    def __init__(self, archivo_csv, directorio_resultados=None):
        """
        Inicializar el analizador de nubosidad
        
        Args:
            archivo_csv (str): Ruta al archivo CSV con datos TMY
            directorio_resultados (str): Directorio donde guardar resultados
        """
        self.archivo_csv = archivo_csv
        self.datos = None
        self.metadatos = {}
        
        # Configurar directorio de resultados
        if directorio_resultados is None:
            # Usar ruta absoluta directa
            self.directorio_resultados = '/home/nicole/UA/OFFGRID/OFFGRID/results/nubosidad'
        else:
            self.directorio_resultados = directorio_resultados
        
        # Crear directorio si no existe
        self._crear_directorio_resultados()
        
        print(f"📁 Directorio de resultados: {self.directorio_resultados}")
    
    def _crear_directorio_resultados(self):
        """Crear directorio de resultados si no existe"""
        try:
            os.makedirs(self.directorio_resultados, exist_ok=True)
            print(f"✅ Directorio creado/verificado: {self.directorio_resultados}")
        except Exception as e:
            print(f"❌ Error creando directorio: {e}")
    
    def cargar_datos(self):
        """Cargar los datos del archivo CSV"""
        print("\n📥 CARGANDO DATOS TMY...")
        
        # Leer datos (saltando metadatos)
        self.datos = pd.read_csv(self.archivo_csv, skiprows=41, encoding='utf-8', engine='python')
        
        # Convertir fecha a datetime
        self.datos['fecha_tmy'] = pd.to_datetime(self.datos['Fecha/Hora'])
        
        # Crear columnas adicionales
        self.datos['año'] = self.datos['fecha_tmy'].dt.year
        self.datos['mes'] = self.datos['fecha_tmy'].dt.month
        self.datos['dia'] = self.datos['fecha_tmy'].dt.day
        self.datos['hora'] = self.datos['fecha_tmy'].dt.hour
        self.datos['dia_año'] = self.datos['fecha_tmy'].dt.dayofyear
        
        print(f"✅ Datos cargados: {len(self.datos)} registros")
        print(f"📅 Período: {self.datos['fecha_tmy'].min()} a {self.datos['fecha_tmy'].max()}")
        
        return self.datos
    
    def calcular_radiacion_teorica(self, latitud=-23.14):
        """Calcular radiación teórica de cielo despejado"""
        print("🔧 Calculando radiación teórica de cielo despejado...")
        
        fechas = self.datos['fecha_tmy'].values
        fechas_dt = pd.to_datetime(fechas)
        
        # Extraer día del año y hora
        dias_año = np.array([fecha.timetuple().tm_yday for fecha in fechas_dt])
        horas = np.array([fecha.hour + fecha.minute/60.0 for fecha in fechas_dt])
        
        # Constante solar
        I0 = 1367
        
        # Corrección por distancia Tierra-Sol
        B = (dias_año - 1) * 2 * np.pi / 365
        correcion_distancia = 1.000110 + 0.034221 * np.cos(B) + 0.001280 * np.sin(B) + \
                             0.000719 * np.cos(2*B) + 0.000077 * np.sin(2*B)
        
        # Declinación solar
        declinacion = np.deg2rad(23.45 * np.sin(np.deg2rad((284 + dias_año) * 360 / 365)))
        
        # Ángulo horario
        lat_rad = np.deg2rad(latitud)
        angulo_horario = np.deg2rad(15 * (horas - 12))
        
        # Ángulo cenital solar
        cos_zenital = (np.sin(lat_rad) * np.sin(declinacion) + 
                      np.cos(lat_rad) * np.cos(declinacion) * np.cos(angulo_horario))
        cos_zenital = np.maximum(cos_zenital, 0)
        
        # Radiación extraterrestre
        radiacion_extraterrestre = I0 * correcion_distancia * cos_zenital
        
        # Modelo de cielo despejado
        transmitancia_atmosferica = 0.75
        ghi_teorico = radiacion_extraterrestre * transmitancia_atmosferica
        
        # Corrección por masa de aire
        altura_solar = np.rad2deg(np.arcsin(cos_zenital))
        masa_aire = np.where(altura_solar > 0, 1 / cos_zenital, 0)
        factor_masa_aire = np.exp(-0.0001 * masa_aire)
        ghi_teorico = ghi_teorico * factor_masa_aire
        
        self.datos['ghi_teorico'] = ghi_teorico
        
        print("✅ Radiación teórica calculada")
        return ghi_teorico
    
    def calcular_indice_claridad(self):
        """Calcular índice de claridad"""
        print("☀️ Calculando índice de claridad...")
        
        if 'ghi_teorico' not in self.datos.columns:
            self.calcular_radiacion_teorica()
        
        # Calcular índice de claridad
        indice_claridad = np.where(self.datos['ghi_teorico'] > 0, 
                                 self.datos['ghi'] / self.datos['ghi_teorico'], 
                                 0)
        indice_claridad = np.clip(indice_claridad, 0, 1.2)
        
        self.datos['indice_claridad'] = indice_claridad
        
        print(f"✅ Índice de claridad calculado")
        print(f"📊 Promedio: {indice_claridad.mean():.3f}")
        print(f"📊 Máximo: {indice_claridad.max():.3f}")
        print(f"📊 Mínimo: {indice_claridad.min():.3f}")
        
        return indice_claridad
    
    def clasificar_dias(self):
        """Clasificar días según nubosidad"""
        print("\n🌤️ CLASIFICANDO DÍAS SEGÚN NUBOSIDAD...")
        
        if 'indice_claridad' not in self.datos.columns:
            self.calcular_indice_claridad()
        
        # Calcular índice promedio diario
        datos_luz = self.datos[self.datos['ghi'] > 0].copy()
        
        clasificacion_diaria = datos_luz.groupby([datos_luz['mes'], datos_luz['dia']]).agg({
            'indice_claridad': 'mean',
            'ghi': ['mean', 'max', 'std'],
            'ghi_teorico': 'mean'
        }).round(3)
        
        clasificacion_diaria.columns = ['indice_claridad_prom', 'ghi_mean', 'ghi_max', 'ghi_std', 'ghi_teorico_mean']
        clasificacion_diaria = clasificacion_diaria.reset_index()
        
        # Clasificar días
        def clasificar_dia(indice):
            if indice >= 0.7:
                return 'Despejado'
            elif indice >= 0.4:
                return 'Parcialmente nuboso'
            else:
                return 'Muy nuboso'
        
        clasificacion_diaria['clasificacion'] = clasificacion_diaria['indice_claridad_prom'].apply(clasificar_dia)
        
        # Agregar fecha
        clasificacion_diaria['fecha'] = pd.to_datetime(
            clasificacion_diaria.apply(lambda x: f"2000-{x['mes']:02d}-{x['dia']:02d}", axis=1)
        )
        
        # Estadísticas
        conteo = clasificacion_diaria['clasificacion'].value_counts()
        total = len(clasificacion_diaria)
        
        print("=" * 60)
        print("📊 CLASIFICACIÓN DE DÍAS:")
        for categoria, cantidad in conteo.items():
            porcentaje = (cantidad / total) * 100
            print(f"   {categoria}: {cantidad} días ({porcentaje:.1f}%)")
        print("=" * 60)
        
        self.clasificacion_diaria = clasificacion_diaria
        return clasificacion_diaria
    
    def analizar_rachas_consecutivas(self):
        """Analizar rachas de días nubosos consecutivos"""
        print("\n☁️ ANALIZANDO RACHAS CONSECUTIVAS...")
        
        if not hasattr(self, 'clasificacion_diaria'):
            self.clasificar_dias()
        
        # Ordenar por fecha
        datos_ordenados = self.clasificacion_diaria.sort_values('fecha').reset_index(drop=True)
        
        def encontrar_rachas(serie, tipo_dia):
            rachas = []
            racha_actual = []
            
            for i, clasificacion in enumerate(serie):
                if clasificacion == tipo_dia:
                    racha_actual.append(i)
                else:
                    if racha_actual:
                        rachas.append(racha_actual.copy())
                        racha_actual = []
            
            if racha_actual:
                rachas.append(racha_actual)
            
            return rachas
        
        # Encontrar rachas
        rachas_muy_nuboso = encontrar_rachas(datos_ordenados['clasificacion'], 'Muy nuboso')
        rachas_parcialmente_nuboso = encontrar_rachas(datos_ordenados['clasificacion'], 'Parcialmente nuboso')
        rachas_despejado = encontrar_rachas(datos_ordenados['clasificacion'], 'Despejado')
        
        # Analizar racha más larga de días muy nubosos
        if rachas_muy_nuboso:
            racha_mas_larga = max(rachas_muy_nuboso, key=len)
            dias_consecutivos_max = len(racha_mas_larga)
            
            inicio_idx = racha_mas_larga[0]
            fin_idx = racha_mas_larga[-1]
            fecha_inicio = datos_ordenados.loc[inicio_idx, 'fecha']
            fecha_fin = datos_ordenados.loc[fin_idx, 'fecha']
            
            print(f"☁️ RACHA MÁS LARGA DE DÍAS MUY NUBOSOS:")
            print(f"   Duración: {dias_consecutivos_max} días consecutivos")
            print(f"   Período: {fecha_inicio.strftime('%d/%m')} - {fecha_fin.strftime('%d/%m')}")
            
            # Detalles de la racha
            print(f"   Detalles día por día:")
            for i, idx in enumerate(racha_mas_larga):
                dia_info = datos_ordenados.loc[idx]
                print(f"     Día {i+1}: {dia_info['fecha'].strftime('%d/%m')} - "
                      f"Índice: {dia_info['indice_claridad_prom']:.3f} - "
                      f"GHI: {dia_info['ghi_mean']:.1f} W/m²")
        else:
            dias_consecutivos_max = 0
            fecha_inicio = None
            fecha_fin = None
        
        # Estadísticas de rachas
        if rachas_muy_nuboso:
            longitudes = [len(racha) for racha in rachas_muy_nuboso]
            print(f"\n📊 ESTADÍSTICAS DE RACHAS MUY NUBOSAS:")
            print(f"   Total de rachas: {len(rachas_muy_nuboso)}")
            print(f"   Racha más larga: {max(longitudes)} días")
            print(f"   Promedio: {np.mean(longitudes):.1f} días")
            
            # Distribución
            contador = Counter(longitudes)
            print(f"   Distribución:")
            for longitud in sorted(contador.keys()):
                print(f"     {longitud} día(s): {contador[longitud]} rachas")
        
        # Implicaciones para sistemas fotovoltaicos
        print(f"\n⚡ IMPLICACIONES PARA SISTEMAS FOTOVOLTAICOS:")
        print("=" * 60)
        if dias_consecutivos_max > 0:
            print(f"🔋 AUTONOMÍA RECOMENDADA: {dias_consecutivos_max + 1} días")
            print(f"⚠️  Días consecutivos máximos muy nubosos: {dias_consecutivos_max}")
        else:
            print("✅ No hay días muy nubosos consecutivos")
            print("🔋 AUTONOMÍA RECOMENDADA: 2-3 días (estándar)")
        print("=" * 60)
        
        # Guardar resultados
        self.rachas_muy_nuboso = rachas_muy_nuboso
        self.rachas_parcialmente_nuboso = rachas_parcialmente_nuboso
        self.rachas_despejado = rachas_despejado
        self.dias_consecutivos_max = dias_consecutivos_max
        
        return {
            'dias_consecutivos_max': dias_consecutivos_max,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'rachas_muy_nuboso': rachas_muy_nuboso,
            'rachas_parcialmente_nuboso': rachas_parcialmente_nuboso,
            'rachas_despejado': rachas_despejado
        }
    
    def encontrar_dias_extremos(self):
        """Encontrar días más despejado y más nuboso"""
        print("\n🔍 IDENTIFICANDO DÍAS EXTREMOS...")
        
        if not hasattr(self, 'clasificacion_diaria'):
            self.clasificar_dias()
        
        # Días extremos
        dia_mas_nuboso = self.clasificacion_diaria.loc[
            self.clasificacion_diaria['indice_claridad_prom'].idxmin()
        ]
        dia_mas_despejado = self.clasificacion_diaria.loc[
            self.clasificacion_diaria['indice_claridad_prom'].idxmax()
        ]
        
        print(f"☁️ DÍA MÁS NUBOSO:")
        print(f"   Fecha: {dia_mas_nuboso['fecha'].strftime('%d/%m')}")
        print(f"   Índice: {dia_mas_nuboso['indice_claridad_prom']:.3f}")
        print(f"   GHI promedio: {dia_mas_nuboso['ghi_mean']:.1f} W/m²")
        
        print(f"\n☀️ DÍA MÁS DESPEJADO:")
        print(f"   Fecha: {dia_mas_despejado['fecha'].strftime('%d/%m')}")
        print(f"   Índice: {dia_mas_despejado['indice_claridad_prom']:.3f}")
        print(f"   GHI promedio: {dia_mas_despejado['ghi_mean']:.1f} W/m²")
        
        self.dia_mas_nuboso = dia_mas_nuboso
        self.dia_mas_despejado = dia_mas_despejado
        
        return dia_mas_despejado, dia_mas_nuboso
    
    def analizar_dia_especifico(self, mes, dia):
        """Analizar nubosidad de un día específico"""
        print(f"\n🔍 ANÁLISIS DETALLADO - {dia}/{mes}")
        
        if 'indice_claridad' not in self.datos.columns:
            self.calcular_indice_claridad()
        
        # Filtrar datos del día
        datos_dia = self.datos[
            (self.datos['mes'] == mes) & (self.datos['dia'] == dia)
        ].copy()
        
        if len(datos_dia) == 0:
            print(f"❌ No se encontraron datos para {dia}/{mes}")
            return None
        
        # Solo horas de luz
        datos_luz = datos_dia[datos_dia['ghi'] > 0]
        
        if len(datos_luz) == 0:
            print(f"❌ No hay horas de luz para {dia}/{mes}")
            return None
        
        # Estadísticas
        indice_promedio = datos_luz['indice_claridad'].mean()
        ghi_max = datos_luz['ghi'].max()
        ghi_teorico_max = datos_luz['ghi_teorico'].max()
        
        # Clasificación
        if indice_promedio >= 0.7:
            clasificacion = 'Despejado'
        elif indice_promedio >= 0.4:
            clasificacion = 'Parcialmente nuboso'
        else:
            clasificacion = 'Muy nuboso'
        
        print(f"📊 Clasificación: {clasificacion}")
        print(f"📊 Índice promedio: {indice_promedio:.3f}")
        print(f"📊 GHI máximo: {ghi_max:.1f} W/m²")
        print(f"📊 Eficiencia máxima: {(ghi_max/ghi_teorico_max)*100:.1f}%")
        
        return {
            'clasificacion': clasificacion,
            'indice_promedio': indice_promedio,
            'ghi_max': ghi_max,
            'datos_dia': datos_dia
        }
    
    def generar_graficos_completos(self):
        """Generar todos los gráficos del análisis"""
        print("\n📊 GENERANDO GRÁFICOS COMPLETOS...")
        
        # Asegurar que todos los análisis estén hechos
        if not hasattr(self, 'clasificacion_diaria'):
            self.clasificar_dias()
        
        if not hasattr(self, 'rachas_muy_nuboso'):
            self.analizar_rachas_consecutivas()
        
        # Gráfico 1: Análisis general de nubosidad
        self._grafico_analisis_general()
        
        # Gráfico 2: Rachas consecutivas
        self._grafico_rachas_consecutivas()
        
        # Gráfico 3: Días extremos
        self._grafico_dias_extremos()
        
        print("✅ Todos los gráficos generados")
    
    def _grafico_analisis_general(self):
        """Gráfico de análisis general de nubosidad"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        colores = {'Despejado': 'gold', 'Parcialmente nuboso': 'orange', 'Muy nuboso': 'gray'}
        
        # Gráfico 1: Índice de claridad anual
        for categoria in colores.keys():
            datos_cat = self.clasificacion_diaria[self.clasificacion_diaria['clasificacion'] == categoria]
            if len(datos_cat) > 0:
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
        
        # Gráfico 2: Distribución porcentual
        conteo = self.clasificacion_diaria['clasificacion'].value_counts()
        colores_pie = [colores[cat] for cat in conteo.index]
        ax2.pie(conteo.values, labels=conteo.index, autopct='%1.1f%%', 
               colors=colores_pie, startangle=90)
        ax2.set_title('Distribución de Días por Nubosidad', fontsize=14, fontweight='bold')
        
        # Gráfico 3: GHI observado vs teórico
        muestra = self.clasificacion_diaria.sample(n=min(50, len(self.clasificacion_diaria)))
        ax3.scatter(muestra['ghi_teorico_mean'], muestra['ghi_mean'], 
                   c=[colores[cat] for cat in muestra['clasificacion']], alpha=0.7, s=50)
        
        max_val = max(muestra['ghi_teorico_mean'].max(), muestra['ghi_mean'].max())
        ax3.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='GHI obs = GHI teórico')
        ax3.set_xlabel('GHI Teórico (W/m²)', fontsize=12)
        ax3.set_ylabel('GHI Observado (W/m²)', fontsize=12)
        ax3.set_title('GHI Observado vs Teórico', fontsize=14, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Gráfico 4: Análisis estacional
        def obtener_estacion(mes):
            if mes in [12, 1, 2]: return 'Verano'
            elif mes in [3, 4, 5]: return 'Otoño'
            elif mes in [6, 7, 8]: return 'Invierno'
            else: return 'Primavera'
        
        self.clasificacion_diaria['estacion'] = self.clasificacion_diaria['mes'].apply(obtener_estacion)
        tabla_estacional = pd.crosstab(self.clasificacion_diaria['estacion'], 
                                     self.clasificacion_diaria['clasificacion'])
        tabla_porcentajes = tabla_estacional.div(tabla_estacional.sum(axis=1), axis=0) * 100
        
        tabla_porcentajes.plot(kind='bar', stacked=True, ax=ax4, 
                              color=[colores[cat] for cat in tabla_porcentajes.columns])
        ax4.set_title('Distribución Estacional de Nubosidad', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Porcentaje (%)', fontsize=12)
        ax4.set_xlabel('Estación', fontsize=12)
        ax4.legend(title='Clasificación')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        archivo = os.path.join(self.directorio_resultados, 'analisis_general_nubosidad.png')
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"💾 Gráfico guardado: {archivo}")
    
    def _grafico_rachas_consecutivas(self):
        """Gráfico de rachas consecutivas"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        colores = {'Despejado': 'gold', 'Parcialmente nuboso': 'orange', 'Muy nuboso': 'gray'}
        
        # Gráfico 1: Timeline de clasificación
        datos_ordenados = self.clasificacion_diaria.sort_values('fecha')
        for _, dia in datos_ordenados.iterrows():
            color = colores[dia['clasificacion']]
            ax1.bar(dia['fecha'], 1, color=color, alpha=0.7, width=1)
        
        ax1.set_title('Clasificación Diaria - Año TMY', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Clasificación', fontsize=12)
        ax1.set_xlabel('Fecha', fontsize=12)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        
        legend_elements = [Patch(facecolor=colores[cat], label=cat) for cat in colores.keys()]
        ax1.legend(handles=legend_elements)
        
        # Gráfico 2: Distribución de rachas muy nubosas
        if self.rachas_muy_nuboso:
            longitudes = [len(racha) for racha in self.rachas_muy_nuboso]
            contador = Counter(longitudes)
            
            longitudes_unicas = sorted(contador.keys())
            frecuencias = [contador[l] for l in longitudes_unicas]
            
            ax2.bar(longitudes_unicas, frecuencias, color='gray', alpha=0.7)
            ax2.set_title('Distribución de Rachas Muy Nubosas', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Días consecutivos', fontsize=12)
            ax2.set_ylabel('Número de rachas', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            max_longitud = max(longitudes)
            ax2.axvline(x=max_longitud, color='red', linestyle='--', linewidth=2, 
                       label=f'Máximo: {max_longitud} días')
            ax2.legend()
        else:
            ax2.text(0.5, 0.5, 'No hay rachas\nmuy nubosas', ha='center', va='center', 
                    transform=ax2.transAxes, fontsize=14)
            ax2.set_title('Distribución de Rachas Muy Nubosas', fontsize=14, fontweight='bold')
        
        # Gráfico 3: Comparación de rachas por tipo
        tipos_rachas = ['Muy nuboso', 'Parcialmente nuboso', 'Despejado']
        datos_rachas_tipos = [self.rachas_muy_nuboso, self.rachas_parcialmente_nuboso, self.rachas_despejado]
        
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
        
        ax3.bar(x - width, max_longitudes, width, label='Máximo', 
               color=['gray', 'orange', 'gold'], alpha=0.7)
        ax3.bar(x, promedios, width, label='Promedio', 
               color=['gray', 'orange', 'gold'], alpha=0.5)
        ax3.bar(x + width, totales, width, label='Total', 
               color=['gray', 'orange', 'gold'], alpha=0.3)
        
        ax3.set_title('Comparación de Rachas por Tipo', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Días / Cantidad', fontsize=12)
        ax3.set_xlabel('Tipo de día', fontsize=12)
        ax3.set_xticks(x)
        ax3.set_xticklabels(tipos_rachas)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Gráfico 4: Información clave
        ax4.text(0.1, 0.8, f'INFORMACIÓN CLAVE:', fontsize=16, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.7, f'☁️ Días muy nubosos consecutivos máximos:', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.15, 0.6, f'{self.dias_consecutivos_max} días', fontsize=20, fontweight='bold', 
                color='red', transform=ax4.transAxes)
        ax4.text(0.1, 0.45, f'🔋 Autonomía recomendada:', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.15, 0.35, f'{self.dias_consecutivos_max + 1} días', fontsize=20, fontweight='bold', 
                color='blue', transform=ax4.transAxes)
        ax4.text(0.1, 0.2, f'📊 Total rachas muy nubosas: {len(self.rachas_muy_nuboso)}', 
                fontsize=12, transform=ax4.transAxes)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        
        plt.tight_layout()
        
        archivo = os.path.join(self.directorio_resultados, 'rachas_consecutivas.png')
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"💾 Gráfico guardado: {archivo}")
    
    def _grafico_dias_extremos(self):
        """Gráfico de análisis de días extremos"""
        if not hasattr(self, 'dia_mas_nuboso'):
            self.encontrar_dias_extremos()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        # Analizar día más nuboso
        mes_nuboso = self.dia_mas_nuboso['mes']
        dia_nuboso = self.dia_mas_nuboso['dia']
        datos_nuboso = self.datos[
            (self.datos['mes'] == mes_nuboso) & (self.datos['dia'] == dia_nuboso) & (self.datos['ghi'] > 0)
        ]
        
        # Gráfico 1: Día más nuboso
        ax1.plot(datos_nuboso['hora'], datos_nuboso['ghi'], 'b-', linewidth=2, 
                label='GHI Observado', marker='o', markersize=4)
        ax1.plot(datos_nuboso['hora'], datos_nuboso['ghi_teorico'], 'r--', linewidth=2, 
                label='GHI Teórico', alpha=0.8)
        ax1.fill_between(datos_nuboso['hora'], datos_nuboso['ghi'], datos_nuboso['ghi_teorico'], 
                        where=(datos_nuboso['ghi'] < datos_nuboso['ghi_teorico']), 
                        color='red', alpha=0.3, label='Pérdida por nubes')
        
        ax1.set_title(f'Día Más Nuboso - {dia_nuboso}/{mes_nuboso}', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Radiación (W/m²)', fontsize=12)
        ax1.set_xlabel('Hora', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Índice de claridad día nuboso
        colores_indice = ['red' if x < 0.4 else 'orange' if x < 0.7 else 'green' 
                         for x in datos_nuboso['indice_claridad']]
        ax2.bar(datos_nuboso['hora'], datos_nuboso['indice_claridad'], 
               color=colores_indice, alpha=0.7)
        ax2.axhline(y=0.7, color='green', linestyle='--', alpha=0.7, label='Despejado')
        ax2.axhline(y=0.4, color='orange', linestyle='--', alpha=0.7, label='Parcialmente nuboso')
        ax2.set_title('Índice de Claridad - Día Más Nuboso', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Índice de Claridad', fontsize=12)
        ax2.set_xlabel('Hora', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1.1)
        
        # Analizar día más despejado
        mes_despejado = self.dia_mas_despejado['mes']
        dia_despejado = self.dia_mas_despejado['dia']
        datos_despejado = self.datos[
            (self.datos['mes'] == mes_despejado) & (self.datos['dia'] == dia_despejado) & (self.datos['ghi'] > 0)
        ]
        
        # Gráfico 3: Día más despejado
        ax3.plot(datos_despejado['hora'], datos_despejado['ghi'], 'b-', linewidth=2, 
                label='GHI Observado', marker='o', markersize=4)
        ax3.plot(datos_despejado['hora'], datos_despejado['ghi_teorico'], 'r--', linewidth=2, 
                label='GHI Teórico', alpha=0.8)
        
        ax3.set_title(f'Día Más Despejado - {dia_despejado}/{mes_despejado}', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Radiación (W/m²)', fontsize=12)
        ax3.set_xlabel('Hora', fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Gráfico 4: Índice de claridad día despejado
        colores_indice_desp = ['red' if x < 0.4 else 'orange' if x < 0.7 else 'green' 
                              for x in datos_despejado['indice_claridad']]
        ax4.bar(datos_despejado['hora'], datos_despejado['indice_claridad'], 
               color=colores_indice_desp, alpha=0.7)
        ax4.axhline(y=0.7, color='green', linestyle='--', alpha=0.7, label='Despejado')
        ax4.axhline(y=0.4, color='orange', linestyle='--', alpha=0.7, label='Parcialmente nuboso')
        ax4.set_title('Índice de Claridad - Día Más Despejado', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Índice de Claridad', fontsize=12)
        ax4.set_xlabel('Hora', fontsize=12)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 1.1)
        
        plt.tight_layout()
        
        archivo = os.path.join(self.directorio_resultados, 'dias_extremos.png')
        plt.savefig(archivo, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"💾 Gráfico guardado: {archivo}")
    
    def generar_reporte_completo(self):
        """Generar reporte completo en texto"""
        print("\n📋 GENERANDO REPORTE COMPLETO...")
        
        # Asegurar que todos los análisis estén hechos
        if not hasattr(self, 'clasificacion_diaria'):
            self.clasificar_dias()
        if not hasattr(self, 'rachas_muy_nuboso'):
            self.analizar_rachas_consecutivas()
        if not hasattr(self, 'dia_mas_nuboso'):
            self.encontrar_dias_extremos()
        
        # Estadísticas
        conteo = self.clasificacion_diaria['clasificacion'].value_counts()
        total_dias = len(self.clasificacion_diaria)
        
        # Crear reporte
        reporte = f"""
ANÁLISIS COMPLETO DE NUBOSIDAD - TMY ANTOFAGASTA
================================================================

PERÍODO ANALIZADO: {self.datos['fecha_tmy'].min().strftime('%Y-%m-%d')} a {self.datos['fecha_tmy'].max().strftime('%Y-%m-%d')}
TOTAL DE REGISTROS: {len(self.datos)} horas
TOTAL DE DÍAS: {total_dias} días

DISTRIBUCIÓN DE DÍAS POR NUBOSIDAD:
================================================================
"""
        
        for categoria in ['Despejado', 'Parcialmente nuboso', 'Muy nuboso']:
            if categoria in conteo.index:
                cantidad = conteo[categoria]
                porcentaje = (cantidad / total_dias) * 100
                reporte += f"• {categoria}: {cantidad} días ({porcentaje:.1f}%)\n"
        
        reporte += f"""
ESTADÍSTICAS DEL ÍNDICE DE CLARIDAD:
================================================================
• Promedio anual: {self.datos['indice_claridad'].mean():.3f}
• Máximo: {self.datos['indice_claridad'].max():.3f}
• Mínimo: {self.datos['indice_claridad'].min():.3f}

DÍAS EXTREMOS:
================================================================
• Día más nuboso: {self.dia_mas_nuboso['fecha'].strftime('%d/%m')} (Índice: {self.dia_mas_nuboso['indice_claridad_prom']:.3f})
• Día más despejado: {self.dia_mas_despejado['fecha'].strftime('%d/%m')} (Índice: {self.dia_mas_despejado['indice_claridad_prom']:.3f})

RACHAS DE DÍAS NUBOSOS CONSECUTIVOS:
================================================================
• Días muy nubosos consecutivos máximos: {self.dias_consecutivos_max} días
• Total de rachas muy nubosas: {len(self.rachas_muy_nuboso)}
"""
        
        if self.rachas_muy_nuboso:
            longitudes = [len(racha) for racha in self.rachas_muy_nuboso]
            reporte += f"• Promedio de duración de rachas: {np.mean(longitudes):.1f} días\n"
            
            contador = Counter(longitudes)
            reporte += "• Distribución de rachas:\n"
            for longitud in sorted(contador.keys()):
                reporte += f"  - {longitud} día(s): {contador[longitud]} rachas\n"
        
        reporte += f"""
IMPLICACIONES PARA SISTEMAS FOTOVOLTAICOS:
================================================================
• AUTONOMÍA RECOMENDADA: {self.dias_consecutivos_max + 1} días
• Antofagasta tiene un excelente recurso solar
• Solo {conteo.get('Muy nuboso', 0)} días muy nubosos en todo el año ({(conteo.get('Muy nuboso', 0)/total_dias*100):.1f}%)
• {conteo.get('Despejado', 0)} días despejados ({(conteo.get('Despejado', 0)/total_dias*100):.1f}%) - Excelente para energía solar

ARCHIVOS GENERADOS:
================================================================
• analisis_general_nubosidad.png - Análisis general
• rachas_consecutivas.png - Análisis de rachas
• dias_extremos.png - Días más nuboso y despejado
• reporte_nubosidad.txt - Este reporte

================================================================
Análisis realizado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Guardar reporte
        archivo_reporte = os.path.join(self.directorio_resultados, 'reporte_nubosidad.txt')
        with open(archivo_reporte, 'w', encoding='utf-8') as f:
            f.write(reporte)
        
        print(f"💾 Reporte guardado: {archivo_reporte}")
        print(reporte)
        
        return reporte
    
    def ejecutar_analisis_completo(self):
        """Ejecutar análisis completo de nubosidad"""
        print("🚀 INICIANDO ANÁLISIS COMPLETO DE NUBOSIDAD")
        print("=" * 70)
        
        # Cargar datos
        self.cargar_datos()
        
        # Calcular índice de claridad
        self.calcular_indice_claridad()
        
        # Clasificar días
        self.clasificar_dias()
        
        # Analizar rachas consecutivas
        self.analizar_rachas_consecutivas()
        
        # Encontrar días extremos
        self.encontrar_dias_extremos()
        
        # Generar gráficos
        self.generar_graficos_completos()
        
        # Generar reporte
        self.generar_reporte_completo()
        
        print("\n✅ ANÁLISIS COMPLETO FINALIZADO")
        print(f"📁 Todos los resultados guardados en: {self.directorio_resultados}")

def main():
    """Función principal"""
    print("🌤️ ANÁLISIS COMPLETO DE NUBOSIDAD - TMY ANTOFAGASTA")
    print("=" * 70)
    
    # Configurar rutas
    archivo_tmy = 'data/DHTMY_E_17WEZY.csv'
    
    # Crear analizador
    analizador = AnalizadorNubosidad(archivo_tmy)
    
    # Ejecutar análisis completo
    analizador.ejecutar_analisis_completo()

if __name__ == "__main__":
    main() 