"""
Script para calcular la capacidad del banco de baterías
basado en días de autonomía y parámetros del sistema.
"""

def calcular_banco_baterias(
    energia_diaria_kwh: float,
    dias_autonomia: int,
    voltaje_sistema: float,
    profundidad_descarga: float,
    voltaje_bateria: float,
    capacidad_bateria_ah: float
):
    """
    Calcula la configuración del banco de baterías según días de autonomía.
    
    Args:
        energia_diaria_kwh: Energía diaria consumida en kWh
        dias_autonomia: Número de días de autonomía deseado
        voltaje_sistema: Voltaje del sistema en V
        profundidad_descarga: Profundidad de descarga (0.0 a 1.0)
        voltaje_bateria: Voltaje nominal de cada batería en V
        capacidad_bateria_ah: Capacidad de cada batería en Ah
    
    Returns:
        dict: Diccionario con los resultados del cálculo
    """
    
    # Cálculo de la capacidad total requerida en Ah
    capacidad_total_ah = (energia_diaria_kwh * 1000 * dias_autonomia) / (voltaje_sistema * profundidad_descarga)
    
    # Cálculo del número de baterías en serie
    num_serie = voltaje_sistema / voltaje_bateria
    
    # Cálculo del número de baterías en paralelo
    num_paralelo = capacidad_total_ah / capacidad_bateria_ah
    
    # Total de baterías necesarias
    total_baterias = num_serie * num_paralelo
    
    # Capacidad real del banco en kWh
    capacidad_real_kwh = (total_baterias * capacidad_bateria_ah * voltaje_bateria) / 1000
    
    return {
        "Capacidad Total [Ah]": capacidad_total_ah,
        "Nº Baterías en Serie": round(num_serie),
        "Nº Baterías en Paralelo": round(num_paralelo),
        "Total Baterías": round(total_baterias),
        "Capacidad Real [kWh]": capacidad_real_kwh,
        "Energía Diaria [kWh]": energia_diaria_kwh,
        "Días de Autonomía": dias_autonomia,
        "Voltaje Sistema [V]": voltaje_sistema,
        "Profundidad Descarga": profundidad_descarga
    }


def imprimir_resultados(resultados):
    """
    Imprime los resultados del cálculo de forma legible.
    """
    print("=" * 60)
    print("CÁLCULO DEL BANCO DE BATERÍAS")
    print("=" * 60)
    print(f"Energía diaria requerida: {resultados['Energía Diaria [kWh]']:.2f} kWh")
    print(f"Días de autonomía: {resultados['Días de Autonomía']}")
    print(f"Voltaje del sistema: {resultados['Voltaje Sistema [V]']} V")
    print(f"Profundidad de descarga: {resultados['Profundidad Descarga']:.1%}")
    print("-" * 60)
    print(f"Capacidad total requerida: {resultados['Capacidad Total [Ah]']:.1f} Ah")
    print(f"Baterías en serie: {resultados['Nº Baterías en Serie']}")
    print(f"Baterías en paralelo: {resultados['Nº Baterías en Paralelo']}")
    print(f"Total de baterías: {resultados['Total Baterías']}")
    print(f"Capacidad real del banco: {resultados['Capacidad Real [kWh]']:.2f} kWh")
    print("=" * 60)


if __name__ == "__main__":
    # Ejemplo de uso
    energia_diaria = 10.0  # kWh
    dias_autonomia = 2
    voltaje_sistema = 48  # V
    profundidad_descarga = 0.8
    voltaje_bateria = 12  # V
    capacidad_bateria = 200  # Ah
    
    resultados = calcular_banco_baterias(
        energia_diaria,
        dias_autonomia,
        voltaje_sistema,
        profundidad_descarga,
        voltaje_bateria,
        capacidad_bateria
    )
    
    imprimir_resultados(resultados) 