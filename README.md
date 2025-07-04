# 🏠 Sistema Fotovoltaico Off-Grid - Simulador

Este proyecto implementa un simulador completo para sistemas fotovoltaicos off-grid con banco de baterías, incluyendo cálculo de capacidad según días de autonomía y simulación del estado de carga (SOC).

## 📁 Estructura del Proyecto

```
proyecto_offgrid/
│
├── data/
│   ├── datos_sistema_fotovoltaico_invierno.csv    # Datos de generación y consumo en invierno
│   └── datos_sistema_fotovoltaico_verano.csv      # Datos de generación y consumo en verano
│
├── scripts/
│   ├── calcular_banco_baterias.py                 # Cálculo de capacidad del banco de baterías
│   ├── simular_soc.py                             # Simulación del estado de carga
│   └── graficar_soc.py                            # Generación de gráficos
│
├── results/                                        # Resultados de las simulaciones
│   ├── soc_invierno.csv
│   ├── soc_verano.csv
│   ├── soc_invierno_diario.png
│   ├── soc_verano_diario.png
│   ├── comparacion_estaciones.png
│   ├── balance_energetico_invierno.png
│   ├── balance_energetico_verano.png
│   └── resumen_estadisticas.txt
│
├── main.py                                         # Script principal
└── README.md                                       # Este archivo
```

## 🚀 Instalación y Uso

### Requisitos

```bash
pip install pandas matplotlib numpy openpyxl
```

### Ejecución

```bash
python main.py
```

## 🔧 Funcionalidades

### 1. Cálculo del Banco de Baterías

El script `calcular_banco_baterias.py` implementa las ecuaciones oficiales para calcular:

- **Capacidad total requerida** en Ah
- **Número de baterías en serie** y paralelo
- **Configuración óptima** del banco

**Ecuaciones utilizadas:**
```
Capacidad Total [Ah] = (Energía Diaria [kWh] × 1000 × Días Autonomía) / (Voltaje Sistema [V] × Profundidad Descarga)
Nº Baterías Serie = Voltaje Sistema / Voltaje Batería
Nº Baterías Paralelo = Capacidad Total / Capacidad Batería
Total Baterías = Nº Serie × Nº Paralelo
```

### 2. Simulación de SOC

El script `simular_soc.py` simula el estado de carga considerando:

- **Generación fotovoltaica** horaria
- **Consumo eléctrico** horario
- **Eficiencias** de carga y descarga
- **Límites** de SOC mínimo y máximo
- **Balance energético** en tiempo real

### 3. Generación de Gráficos

El script `graficar_soc.py` crea visualizaciones de:

- **SOC diario** con generación y consumo
- **Comparación entre estaciones** (invierno vs verano)
- **Balance energético** con áreas de exceso y déficit
- **Simulación multi-día** para análisis de autonomía

## 📊 Parámetros Configurables

### Parámetros del Sistema
- `dias_autonomia`: Días de autonomía (1, 2, 3, 5...)
- `voltaje_sistema`: Voltaje del sistema (12V, 24V, 48V)
- `profundidad_descarga`: Profundidad de descarga (0.5 - 0.8)
- `voltaje_bateria`: Voltaje nominal de cada batería
- `capacidad_bateria_ah`: Capacidad de cada batería en Ah

### Parámetros de Simulación
- `soc_inicial`: SOC inicial (0.0 - 1.0)
- `soc_minimo`: SOC mínimo permitido (0.1 - 0.3)
- `eficiencia_carga`: Eficiencia de carga (0.8 - 0.95)
- `eficiencia_descarga`: Eficiencia de descarga (0.8 - 0.95)

## 📈 Análisis de Resultados

### Métricas Calculadas
- **SOC mínimo, máximo y promedio**
- **Horas críticas** (SOC < 30%)
- **Energía cargada y descargada**
- **Eficiencia del sistema**

### Gráficos Generados
1. **SOC Diario**: Estado de carga con generación y consumo
2. **Comparación Estacional**: Invierno vs Verano
3. **Balance Energético**: Excesos y déficits
4. **Simulación Multi-día**: Análisis de autonomía

## 🔄 Modificación de Días de Autonomía

Para cambiar los días de autonomía, edita esta línea en `main.py`:

```python
PARAMETROS_DEFAULT = {
    'dias_autonomia': 2,  # Cambia aquí: 1, 2, 3, 5...
    # ... otros parámetros
}
```

O ejecuta la simulación múltiple que prueba automáticamente 1, 2, 3 y 5 días.

## 📋 Ejemplo de Uso

```python
# Ejecutar simulación con parámetros personalizados
ejecutar_simulacion_completa(
    dias_autonomia=3,
    voltaje_sistema=48,
    profundidad_descarga=0.8,
    voltaje_bateria=12,
    capacidad_bateria_ah=200
)
```

## 📊 Interpretación de Resultados

### SOC Crítico
- **SOC < 20%**: Batería en riesgo de descarga profunda
- **SOC < 30%**: Nivel crítico, considerar aumentar autonomía
- **SOC > 80%**: Batería bien cargada

### Eficiencia del Sistema
- **Eficiencia > 85%**: Sistema bien dimensionado
- **Eficiencia < 70%**: Considerar optimizaciones

### Horas Críticas
- **0-2 horas**: Sistema bien dimensionado
- **3-6 horas**: Considerar aumentar autonomía
- **>6 horas**: Sistema subdimensionado

## 🛠️ Personalización

### Agregar Nuevos Datos
1. Coloca archivos CSV en `data/`
2. Asegúrate de que tengan columnas: `Hora`, `Generacion_PV`, `Consumo`
3. Modifica `main.py` para cargar tus datos

### Modificar Parámetros de Batería
Edita los parámetros en `main.py` según tus baterías específicas:
- Voltaje nominal
- Capacidad en Ah
- Profundidad de descarga recomendada

### Agregar Nuevos Gráficos
Extiende `graficar_soc.py` con nuevas funciones de visualización.

## 📝 Notas Técnicas

- Los datos de entrada deben ser horarios (24 registros por día)
- La generación fotovoltaica debe estar en Watts
- El consumo debe estar en Watts
- Los resultados se guardan automáticamente en `results/`

## 🤝 Contribuciones

Para contribuir al proyecto:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

**Desarrollado para análisis de sistemas fotovoltaicos off-grid con enfoque en autonomía energética.** 