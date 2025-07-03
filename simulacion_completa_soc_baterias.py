
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Parámetros del sistema
capacidad_bateria_kwh = 10
soc_min = 0.2
soc_max = 1.0
soc_inicial = soc_max

# Cargar archivos
df_inv = pd.read_csv("datos_sistema_fotovoltaico_invierno.csv")
df_ver = pd.read_csv("datos_sistema_fotovoltaico_verano.csv")
df_load_raw = pd.read_excel("cargas_opt.xlsx")

# Calcular carga total y convertir a paso horario
df_load_raw["Consumo"] = df_load_raw.iloc[:, 1:].sum(axis=1)
df_load_raw["Hora"] = pd.date_range(start="2025-06-21", periods=len(df_load_raw), freq="30min")
df_load_hourly = df_load_raw.resample("H", on="Hora").sum().reset_index()[["Hora", "Consumo"]]

# Extender carga a 3 días
df_load_3dias = pd.concat([df_load_hourly.copy() for _ in range(3)], ignore_index=True)
df_load_3dias["Hora"] = pd.date_range(start="2025-06-21", periods=len(df_load_3dias), freq="H")

# Función para extender datos solares a 3 días
def extender_tres_dias(df, start_date):
    df = df.copy()
    df["Hora"] = pd.date_range(start=start_date, periods=len(df), freq="30min")
    df_ext = pd.concat([df.copy() for _ in range(3)], ignore_index=True)
    df_ext["Hora"] = pd.date_range(start=start_date, periods=len(df_ext), freq="30min")
    return df_ext.resample("H", on="Hora").sum().reset_index()

# Aplicar extensión y agregación horaria
inv_horario = extender_tres_dias(df_inv, "2025-06-21")
ver_horario = extender_tres_dias(df_ver, "2025-12-21")

# Simulación SOC
def simular_soc(df_gen, df_load):
    soc = [soc_inicial]
    energia_bateria = [soc_inicial * capacidad_bateria_kwh]
    for i in range(len(df_gen)):
        gen_kwh = df_gen.loc[i, "Generacion_PV"] / 1000
        consumo_kwh = df_load.loc[i, "Consumo"] / 1000
        delta = gen_kwh - consumo_kwh
        energia_actual = energia_bateria[-1] + delta
        energia_actual = min(max(energia_actual, soc_min * capacidad_bateria_kwh), soc_max * capacidad_bateria_kwh)
        energia_bateria.append(energia_actual)
        soc.append(energia_actual / capacidad_bateria_kwh)
    return pd.DataFrame({
        "Hora": df_load["Hora"],
        "Generacion_PV": df_gen["Generacion_PV"],
        "Consumo": df_load["Consumo"],
        "SOC": soc[1:]
    })

# Ejecutar simulación
df_soc_inv = simular_soc(inv_horario, df_load_3dias)
df_soc_ver = simular_soc(ver_horario, df_load_3dias)

# Guardar CSV
df_soc_inv.to_csv("soc_invierno_3dias_CORREGIDO.csv", index=False)
df_soc_ver.to_csv("soc_verano_3dias_CORREGIDO.csv", index=False)

# Graficar invierno
fig, ax1 = plt.subplots(figsize=(14, 6))
ax1.plot(df_soc_inv["Hora"], df_soc_inv["Generacion_PV"], label="Generación FV (invierno)", color="purple")
ax1.plot(df_soc_inv["Hora"], df_soc_inv["Consumo"], label="Consumo", linestyle="--", color="black")
ax1.set_ylabel("Potencia (W)")
ax1.set_xlabel("Hora")
ax1.legend(loc="upper left")
ax1.grid(True)
ax2 = ax1.twinx()
ax2.plot(df_soc_inv["Hora"], df_soc_inv["SOC"], label="SOC invierno", color="blue")
ax2.set_ylabel("SOC")
ax2.legend(loc="upper right")
plt.title("Generación FV, Consumo y SOC – Invierno (3 días)")
plt.tight_layout()
plt.savefig("grafico_soc_invierno_3dias.png", dpi=300)

# Graficar verano
fig, ax3 = plt.subplots(figsize=(14, 6))
ax3.plot(df_soc_ver["Hora"], df_soc_ver["Generacion_PV"], label="Generación FV (verano)", color="green")
ax3.plot(df_soc_ver["Hora"], df_soc_ver["Consumo"], label="Consumo", linestyle="--", color="black")
ax3.set_ylabel("Potencia (W)")
ax3.set_xlabel("Hora")
ax3.legend(loc="upper left")
ax3.grid(True)
ax4 = ax3.twinx()
ax4.plot(df_soc_ver["Hora"], df_soc_ver["SOC"], label="SOC verano", color="orange")
ax4.set_ylabel("SOC")
ax4.legend(loc="upper right")
plt.title("Generación FV, Consumo y SOC – Verano (3 días)")
plt.tight_layout()
plt.savefig("grafico_soc_verano_3dias.png", dpi=300)

plt.show()
