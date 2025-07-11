#!/usr/bin/env python3
import pandas as pd
import matplotlib
# usar backend no interactivo de forma explícita (opcional)
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    input_xlsx = "/home/nicole/UA/OFFGRID/OFFGRID/data/cargas_opt.xlsx"
    output_png = "/home/nicole/UA/OFFGRID/OFFGRID/results/consumo_familiar_diario.png"

    print("🔍 DIAGNÓSTICO DE DATOS DE CARGA")
    print("=" * 50)
    
    # Cargar datos
    print(f"📁 Leyendo archivo: {input_xlsx}")
    df = pd.read_excel(input_xlsx, header=0)
    print(f"✅ Datos cargados: {len(df)} filas x {len(df.columns)} columnas")
    
    # Mostrar estructura de datos
    print(f"\n📊 ESTRUCTURA DE DATOS:")
    print(f"   Columnas disponibles: {list(df.columns)}")
    print(f"   Tipos de datos:")
    for col in df.columns:
        print(f"     {col}: {df[col].dtype}")
    
    # Mostrar primeros registros
    print(f"\n📋 PRIMEROS 5 REGISTROS:")
    print(df.head())
    
    # Verificar datos faltantes
    print(f"\n❓ DATOS FALTANTES:")
    for col in df.columns:
        faltantes = df[col].isnull().sum()
        if faltantes > 0:
            print(f"   {col}: {faltantes} valores faltantes")
        else:
            print(f"   {col}: Sin datos faltantes")
    
    # Procesar datos
    carga_cols = [c for c in df.columns if c.lower() != "hora"]
    print(f"\n🔧 PROCESANDO DATOS:")
    print(f"   Columnas de carga: {carga_cols}")
    print(f"   Total de columnas de carga: {len(carga_cols)}")
    
    # Convertir hora
    df["Hour"] = df["Hora"].astype(float).apply(lambda x: int(x))
    print(f"   Horas únicas: {sorted(df['Hour'].unique())}")
    
    # Agrupar por hora
    df_hourly = df.groupby("Hour")[carga_cols].sum()
    print(f"\n📈 DATOS AGRUPADOS POR HORA:")
    print(f"   Filas resultantes: {len(df_hourly)}")
    print(f"   Columnas: {list(df_hourly.columns)}")
    
    # Mostrar algunos valores
    print(f"\n📊 VALORES DE CARGA POR HORA:")
    for hora in df_hourly.index[:5]:  # Primeras 5 horas
        valores = df_hourly.loc[hora]
        print(f"   {hora:02d}:00 → {valores.to_dict()}")
    
    # Formatear índice
    df_hourly.index = df_hourly.index.map(lambda h: f"{h:02d}:00")
    df_hourly["Total"] = df_hourly.sum(axis=1)
    
    print(f"\n📊 TOTALES POR HORA:")
    for hora, total in df_hourly["Total"].items():
        print(f"   {hora} → {total:.1f} W")
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   Consumo máximo: {df_hourly['Total'].max():.1f} W")
    print(f"   Consumo mínimo: {df_hourly['Total'].min():.1f} W")
    print(f"   Consumo promedio: {df_hourly['Total'].mean():.1f} W")
    print(f"   Consumo total diario: {df_hourly['Total'].sum():.1f} Wh")

    fig, ax = plt.subplots(figsize=(18, 9))
    df_hourly[carga_cols].plot(kind="bar", stacked=True, ax=ax, colormap="tab20", width=0.5)

    y_max = df_hourly["Total"].max()
    for idx, val in enumerate(df_hourly["Total"]):
        ax.text(idx, val + y_max * 0.01, f"{val:.0f}", ha="center", va="bottom", fontsize=16, fontweight="bold")

    total_diario = df_hourly["Total"].sum()
    ax.text(len(df_hourly) - 1, y_max,
            f"Energía Total\nconsumida del Día: {total_diario:.1f} Wh",
            ha="right", va="top", fontsize=14, fontweight="bold")

    ax.set_xlabel("Hora del día", fontsize=20, fontweight="bold")
    ax.set_ylabel("Potencia (W)", fontsize=20, fontweight="bold")
    ax.set_title("Perfil de consumo diario para modelación", fontsize=22, fontweight="bold")
    ax.set_xticklabels(df_hourly.index, rotation=45, fontsize=16)
    ax.legend(title="Artefactos", loc="upper left", bbox_to_anchor=(0, 1), fontsize=16)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    print(f"\n💾 GUARDANDO GRÁFICO:")
    print(f"   Archivo: {output_png}")
    print(f"   Resolución: 600 DPI")
    
    fig.savefig(output_png, dpi=600)
    plt.close(fig)  # cierra la figura tras guardarla
    
    print(f"\n✅ PROCESAMIENTO COMPLETADO!")
    print("=" * 50)

if __name__ == "__main__":
    main()

