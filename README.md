# Sistema Fotovoltaico Sin Batería - Análisis Energético

Este proyecto analiza el comportamiento de un sistema fotovoltaico sin batería, comparando la generación solar con el consumo familiar para determinar excesos y déficits energéticos.

## 📁 Archivos del Proyecto

### Datos de Entrada
- **`Recurso_solar.xlsx`**: Datos de irradiancia solar por hora
  - `Hora`: Horas del día (0-23)
  - `GHI_W_m2`: Irradiancia horizontal global (W/m²)
  - `Gmod`: Irradiancia inclinada en el módulo (W/m²)
  - `Porcentaje_Mejora`: Mejora porcentual por inclinación

- **`cargas.xlsx`**: Datos de consumo eléctrico por electrodoméstico
  - `Hora`: Intervalos de media hora (0.0, 0.5, 1.0, 1.5, ...)
  - Columnas de electrodomésticos: TV, Iluminación, Decodificador, Microondas, etc.

### Scripts de Análisis
- **`grafico_completo_sin_bateria.py`**: Script principal que genera el análisis completo
- **`calculo_carga.py`**: Script auxiliar para análisis de consumo
- **`Calculos_Carga.ipynb`**: Notebook de referencia profesional

## ⚙️ Especificaciones del Sistema Fotovoltaico

```
• Número de módulos: 10
• Potencia por módulo: 300 Wp
• Capacidad total instalada: 3.0 kWp
• Eficiencia del módulo: 18%
• Área por módulo: 1.6 m²
• Área total de módulos: 16.0 m²
• Pérdidas del sistema: 4%
```

## 🔄 Procesamiento de Datos

### 1. Problema de Resolución Temporal
**Desafío inicial:** Los datos tenían diferentes resoluciones temporales:
- Datos solares: 24 puntos (cada hora)
- Datos de consumo: 48 puntos (cada media hora)

**Solución implementada:** En lugar de interpolar el consumo (perdiendo información), expandimos los datos solares a resolución de medias horas:

```python
# Expandir datos solares a resolución de medias horas
horas_expandidas = df_cargas['Hora'].values  # 48 puntos
ghi_expandido = np.interp(horas_expandidas, df_solar['Hora'], df_solar['GHI_W_m2'])
gmod_expandido = np.interp(horas_expandidas, df_solar['Hora'], df_solar['Gmod'])
```

### 2. Cálculo de Generación Fotovoltaica

La generación se calcula usando la fórmula:

```python
Generacion_PV = Gmod × Área_módulo × Eficiencia × Num_módulos × (1 - Pérdidas)
```

Donde:
- `Gmod`: Irradiancia inclinada (W/m²)
- `Área_módulo`: 1.6 m² por módulo
- `Eficiencia`: 18% (0.18)
- `Num_módulos`: 10
- `Pérdidas`: 4% (0.04)

### 3. Procesamiento del Consumo

```python
# Agrupar consumo por electrodoméstico
carga_cols = [c for c in df_cargas.columns if c.lower() != 'hora']
df_hourly = df_cargas.groupby(df_cargas['Hora'].astype(float))[carga_cols].sum()
df_hourly['Total_Consumo'] = df_hourly.sum(axis=1)
```

### 4. Cálculo de Energía Disponible

La energía disponible se calcula como la diferencia entre generación y consumo:

```python
diferencia_energia = Generacion_PV - Consumo
```

**Interpretación:**
- `diferencia_energia > 0`: Exceso energético (se puede vender o almacenar)
- `diferencia_energia < 0`: Déficit energético (se debe comprar de la red)
- `diferencia_energia = -Consumo` cuando `Generacion_PV = 0` (horas nocturnas)

## 📊 Generación de Gráficos

El script genera un gráfico de tres paneles que muestra:

### Panel 1: Irradiancia Solar
```python
ax1.plot(df_expandido['Hora'], df_expandido['GHI_W_m2'], 'b-', linewidth=2)
ax1.fill_between(df_expandido['Hora'], df_expandido['GHI_W_m2'], alpha=0.3, color='tab:blue')
```
- **Curva azul**: Irradiancia horizontal global (GHI)
- **Curva verde**: Irradiancia inclinada (Gmod)
- **Áreas sombreadas**: Energía solar disponible

### Panel 2: Consumo Familiar
```python
ax2.step(df_expandido['Hora'], df_expandido['Consumo'], where='pre', color='red')
ax2.fill_between(df_expandido['Hora'], 0, df_expandido['Consumo'], 
                 alpha=0.3, color='red', step='pre')
```
- **Escalones rojos**: Consumo por intervalos de media hora
- `step='pre'`: Representa el consumo constante durante cada intervalo

### Panel 3: Generación vs Consumo
```python
# Generación fotovoltaica (curva suave)
ax3.plot(df_expandido['Hora'], df_expandido['Generacion_PV'], 
         linewidth=2, color='tab:purple')

# Consumo (escalones)
ax3.step(df_expandido['Hora'], df_expandido['Consumo'], 
         where='pre', color='tab:red')

# Línea de energía disponible
ax3.plot(df_expandido['Hora'], diferencia_energia, 
         color='tab:orange', linewidth=2)
```

## 🎨 Visualización de Excesos y Déficits

### Problema Técnico Resuelto
**Desafío:** Los cambios abruptos en la diferencia energética causaban "gaps" en las áreas de relleno.

**Ejemplo crítico:**
- Hora 8.0: Diferencia = -626.3W (déficit)
- Hora 9.0: Diferencia = +676.2W (exceso)

**Solución implementada:**
```python
# Rellenar toda el área de diferencia con colores condicionales
ax3.fill_between(df_expandido['Hora'], 0, diferencia_energia, 
                 where=(diferencia_energia >= 0),
                 alpha=0.3, color='green', interpolate=True,
                 label=f'Exceso = {energia_exceso_total:.2f} kWh')

ax3.fill_between(df_expandido['Hora'], 0, diferencia_energia, 
                 where=(diferencia_energia < 0),
                 alpha=0.3, color='red', interpolate=True,
                 label=f'Déficit = {energia_deficit_total:.2f} kWh')
```

### Interpretación Visual
- **Área verde**: Energía excedente que se puede vender o almacenar
- **Área roja**: Energía deficitaria que se debe comprar de la red
- **Línea naranja**: Energía disponible momento a momento
- **Sin gaps**: Las áreas son complementarias y cubren toda la diferencia

## 📈 Cálculo de Energías Totales

### Integración Numérica
Usamos la regla del trapecio para calcular las energías totales:

```python
# Energía generada
energia_pv_total = np.trapz(df_expandido['Generacion_PV'], df_expandido['Hora'])/1000

# Energía consumida
energia_consumo_total = np.trapz(df_expandido['Consumo'], df_expandido['Hora'])/1000

# Energía excedente
energia_disponible_positiva = diferencia_energia.clip(lower=0)
energia_exceso_total = np.trapz(energia_disponible_positiva, df_expandido['Hora'])/1000

# Energía deficitaria
energia_disponible_negativa = diferencia_energia.clip(upper=0)
energia_deficit_total = abs(np.trapz(energia_disponible_negativa, df_expandido['Hora'])/1000)
```

### Balance Energético
```python
balance_energetico = energia_pv_total - energia_consumo_total
```

**Interpretación:**
- `balance > 0`: Sistema sobredimensionado (genera más de lo que consume)
- `balance < 0`: Sistema subdimensionado (consume más de lo que genera)
- `balance = 0`: Sistema perfectamente dimensionado

## 🚀 Cómo Ejecutar el Análisis

1. **Preparar los datos:**
   ```bash
   # Asegúrate de tener los archivos Excel en el directorio
   ls Recurso_solar.xlsx cargas.xlsx
   ```

2. **Ejecutar el análisis:**
   ```bash
   python3 grafico_completo_sin_bateria.py
   ```

3. **Resultados generados:**
   - Gráfico de tres paneles guardado como imagen
   - Resumen energético impreso en consola
   - Análisis de sobredimensionamiento/subdimensionamiento

## 📋 Resultados Típicos

```
ESPECIFICACIONES DEL SISTEMA:
• Módulos: 10 x 300W
• Capacidad instalada: 3000 Wp (3.0 kWp)
• Eficiencia del módulo: 18.0%
• Área total de módulos: 16.0 m²
• Pérdidas del sistema: 4.0%

RESULTADOS ENERGÉTICOS:
• Energía solar disponible (GHI): 4.50 kWh/m²·día
• Energía solar inclinada (Gmod): 5.86 kWh/m²·día
• Generación fotovoltaica total: 16.19 kWh/día
• Consumo total: 12.35 kWh/día
• Energía excedente: 12.18 kWh/día
• Energía déficit: 8.34 kWh/día
• Balance energético: 3.84 kWh/día

✅ SISTEMA SOBREDIMENSIONADO: La generación supera el consumo
```

## 🔧 Consideraciones Técnicas

### Precisión Temporal
- **Resolución final**: 48 puntos por día (cada 30 minutos)
- **Ventaja**: Captura cambios abruptos en consumo y transiciones exactas
- **Desventaja**: Interpolación suaviza la irradiancia solar

### Limitaciones
1. **Datos de irradiancia**: Originalmente por hora, interpolados a medias horas
2. **Pérdidas del sistema**: Valor fijo del 4% (podría variar según condiciones)
3. **Sin almacenamiento**: No considera baterías ni gestión de excesos

### Validaciones Implementadas
- ✅ Energía disponible = -Consumo cuando Generación = 0
- ✅ Transiciones exactas entre exceso y déficit
- ✅ Áreas complementarias sin gaps
- ✅ Balance energético coherente

## 👥 Créditos

Desarrollado para análisis de sistemas fotovoltaicos sin batería, con enfoque en precisión temporal y visualización clara de excesos/déficits energéticos.

---
*Para más información o soporte técnico, consulta los comentarios en el código fuente.* 