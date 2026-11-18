"""
Genera las gráficas de la Fase 2 para el documento y el video:
  - funciones de pertenencia de las 2 entradas y la salida
  - mapa de calor con el puntaje para todas las combinaciones de entrada

Uso (desde la raíz del repo):
    python -m fuzzy.graficas
Las imágenes quedan en docs/img/.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventana: solo guardar archivos
import matplotlib.pyplot as plt
import numpy as np

from fuzzy.motor import errores, evaluar, mantenimiento, tiempo

SALIDA = Path(__file__).resolve().parent.parent / "docs" / "img"
COLORES = ["#2e7d32", "#f9a825", "#c62828"]  # verde, ámbar, rojo


def graficar_variable(variable, titulo, eje_x, archivo):
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for (nombre, termino), color in zip(variable.terms.items(), COLORES):
        ax.plot(variable.universe, termino.mf, linewidth=2.2, color=color, label=nombre)
        ax.fill_between(variable.universe, termino.mf, alpha=0.12, color=color)
    ax.set_title(titulo, fontsize=12, fontweight="bold")
    ax.set_xlabel(eje_x)
    ax.set_ylabel("Grado de pertenencia")
    ax.set_ylim(-0.02, 1.08)
    ax.grid(alpha=0.25)
    ax.legend(loc="center right", frameon=False)
    fig.tight_layout()
    fig.savefig(SALIDA / archivo, dpi=150)
    plt.close(fig)


def graficar_mapa(archivo):
    ts = np.linspace(0, 10, 41)
    es = np.linspace(0, 50, 41)
    z = np.array([[evaluar(t, e)["puntaje"] for t in ts] for e in es])
    fig, ax = plt.subplots(figsize=(7, 4.6))
    im = ax.imshow(z, origin="lower", aspect="auto", cmap="RdYlGn_r",
                   extent=[ts[0], ts[-1], es[0], es[-1]], vmin=0, vmax=100)
    cs = ax.contour(ts, es, z, levels=[35, 65], colors="black", linewidths=0.8, linestyles="--")
    ax.clabel(cs, fmt="%d", fontsize=8)
    ax.set_title("Necesidad de mantenimiento (0 = al día, 100 = urgente)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Tiempo de carga (s)")
    ax.set_ylabel("Errores de sintaxis")
    fig.colorbar(im, ax=ax, label="Puntaje difuso")
    fig.tight_layout()
    fig.savefig(SALIDA / archivo, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    graficar_variable(tiempo, "Entrada 1: Tiempo de carga", "Segundos", "fuzzy_tiempo_carga.png")
    graficar_variable(errores, "Entrada 2: Errores de sintaxis", "Cantidad de errores", "fuzzy_errores.png")
    graficar_variable(mantenimiento, "Salida: Nivel de mantenimiento", "Puntaje (0-100)", "fuzzy_mantenimiento.png")
    graficar_mapa("fuzzy_mapa_decision.png")
    print("Gráficas guardadas en", SALIDA)
