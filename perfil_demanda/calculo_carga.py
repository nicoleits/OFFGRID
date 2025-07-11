#!/usr/bin/env python3
import pandas as pd
import matplotlib
# usar backend no interactivo de forma explícita (opcional)
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    input_xlsx = "/home/nicole/UA/OFFGRID/OFFGRID/data/cargas.xlsx"
    output_png = "/home/nicole/UA/OFFGRID/OFFGRID/results/consumo_familiar_diario.png"

    df = pd.read_excel(input_xlsx, header=0)
    carga_cols = [c for c in df.columns if c.lower() != "hora"]
    df["Hour"] = df["Hora"].astype(float).apply(lambda x: int(x))
    df_hourly = df.groupby("Hour")[carga_cols].sum()
    df_hourly.index = df_hourly.index.map(lambda h: f"{h:02d}:00")
    df_hourly["Total"] = df_hourly.sum(axis=1)

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

    fig.savefig(output_png, dpi=600)
    plt.close(fig)  # cierra la figura tras guardarla

if __name__ == "__main__":
    main()

