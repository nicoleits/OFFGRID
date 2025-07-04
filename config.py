"""
Archivo de configuración centralizada para el sistema fotovoltaico off-grid.
Aquí puedes modificar todos los parámetros del sistema de forma fácil.
"""

# =============================================================================
# PARÁMETROS DEL SISTEMA DE BATERÍAS
# =============================================================================

# Configuración del banco de baterías
PARAMETROS_BATERIAS = {
    'voltaje_sistema': 48,          # Voltaje del sistema (V)
    'profundidad_descarga': 0.8,    # Profundidad de descarga (0.0 - 1.0)
    'voltaje_bateria': 12,          # Voltaje nominal de cada batería (V)
    'capacidad_bateria_ah': 200,    # Capacidad de cada batería (Ah)
}

# =============================================================================
# PARÁMETROS DE SIMULACIÓN
# =============================================================================

# Configuración de la simulación SOC
PARAMETROS_SIMULACION = {
    'soc_inicial': 1.0,             # SOC inicial (0.0 - 1.0)
    'soc_minimo': 0.2,              # SOC mínimo permitido (0.0 - 1.0)
    'eficiencia_carga': 0.9,        # Eficiencia de carga (0.0 - 1.0)
    'eficiencia_descarga': 0.9,     # Eficiencia de descarga (0.0 - 1.0)
}

# =============================================================================
# PARÁMETROS DE ANÁLISIS
# =============================================================================

# Días de autonomía a analizar
DIAS_AUTONOMIA_ANALISIS = [1, 2, 3, 5, 7]

# Umbrales para evaluación del sistema
UMBRALES_EVALUACION = {
    'soc_critico': 0.3,             # SOC considerado crítico
    'soc_minimo_aceptable': 0.2,    # SOC mínimo aceptable
    'eficiencia_optima': 0.85,      # Eficiencia óptima del sistema
    'eficiencia_minima': 0.70,      # Eficiencia mínima aceptable
    'horas_criticas_maximas': 6,    # Máximo de horas críticas aceptables
}

# =============================================================================
# CONFIGURACIÓN DE ARCHIVOS
# =============================================================================

# Rutas de archivos de datos
RUTAS_DATOS = {
    'invierno': 'data/datos_sistema_fotovoltaico_invierno.csv',
    'verano': 'data/datos_sistema_fotovoltaico_verano.csv',
}

# Rutas de resultados
RUTAS_RESULTADOS = {
    'directorio': 'results/',
    'soc_invierno': 'results/soc_invierno.csv',
    'soc_verano': 'results/soc_verano.csv',
    'comparacion': 'results/comparacion_dias_autonomia.csv',
    'reporte': 'results/reporte_comparativo.txt',
}

# =============================================================================
# CONFIGURACIÓN DE GRÁFICOS
# =============================================================================

# Configuración de visualización
CONFIG_GRAFICOS = {
    'figsize': (14, 8),
    'dpi': 300,
    'estilo': 'default',
    'colores': {
        'invierno': 'blue',
        'verano': 'orange',
        'generacion': 'green',
        'consumo': 'red',
        'soc': 'purple',
        'balance_positivo': 'lightgreen',
        'balance_negativo': 'lightcoral',
    }
}

# =============================================================================
# FUNCIONES DE CONFIGURACIÓN
# =============================================================================

def obtener_parametros_completos(dias_autonomia=2):
    """
    Obtiene todos los parámetros combinados para una simulación.
    
    Args:
        dias_autonomia: Número de días de autonomía
    
    Returns:
        dict: Diccionario con todos los parámetros
    """
    return {
        'dias_autonomia': dias_autonomia,
        **PARAMETROS_BATERIAS,
        **PARAMETROS_SIMULACION
    }

def validar_parametros():
    """
    Valida que todos los parámetros estén dentro de rangos aceptables.
    
    Returns:
        bool: True si todos los parámetros son válidos
    """
    errores = []
    
    # Validar parámetros de baterías
    if PARAMETROS_BATERIAS['voltaje_sistema'] not in [12, 24, 48]:
        errores.append("Voltaje del sistema debe ser 12, 24 o 48V")
    
    if not 0.5 <= PARAMETROS_BATERIAS['profundidad_descarga'] <= 0.8:
        errores.append("Profundidad de descarga debe estar entre 0.5 y 0.8")
    
    if PARAMETROS_BATERIAS['voltaje_bateria'] <= 0:
        errores.append("Voltaje de batería debe ser positivo")
    
    if PARAMETROS_BATERIAS['capacidad_bateria_ah'] <= 0:
        errores.append("Capacidad de batería debe ser positiva")
    
    # Validar parámetros de simulación
    if not 0 <= PARAMETROS_SIMULACION['soc_inicial'] <= 1:
        errores.append("SOC inicial debe estar entre 0 y 1")
    
    if not 0 <= PARAMETROS_SIMULACION['soc_minimo'] <= 1:
        errores.append("SOC mínimo debe estar entre 0 y 1")
    
    if not 0.8 <= PARAMETROS_SIMULACION['eficiencia_carga'] <= 1:
        errores.append("Eficiencia de carga debe estar entre 0.8 y 1")
    
    if not 0.8 <= PARAMETROS_SIMULACION['eficiencia_descarga'] <= 1:
        errores.append("Eficiencia de descarga debe estar entre 0.8 y 1")
    
    # Mostrar errores si los hay
    if errores:
        print("❌ Errores en la configuración:")
        for error in errores:
            print(f"  - {error}")
        return False
    
    print("✅ Configuración válida")
    return True

def imprimir_configuracion():
    """
    Imprime la configuración actual del sistema.
    """
    print("="*60)
    print("CONFIGURACIÓN ACTUAL DEL SISTEMA")
    print("="*60)
    
    print("\n🔋 PARÁMETROS DE BATERÍAS:")
    for param, valor in PARAMETROS_BATERIAS.items():
        print(f"  - {param}: {valor}")
    
    print("\n⚡ PARÁMETROS DE SIMULACIÓN:")
    for param, valor in PARAMETROS_SIMULACION.items():
        print(f"  - {param}: {valor}")
    
    print("\n📊 DÍAS DE AUTONOMÍA A ANALIZAR:")
    print(f"  - {DIAS_AUTONOMIA_ANALISIS}")
    
    print("\n🎯 UMBRALES DE EVALUACIÓN:")
    for param, valor in UMBRALES_EVALUACION.items():
        print(f"  - {param}: {valor}")
    
    print("="*60)

if __name__ == "__main__":
    # Validar y mostrar configuración
    imprimir_configuracion()
    validar_parametros() 