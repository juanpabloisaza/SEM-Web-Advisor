"""
Fase 2: el cerebro difuso de SEM-Web-Advisor (scikit-fuzzy).

Convierte dos datos técnicos que mide el Agente Analista en un veredicto
lingüístico que entiende cualquier persona:

    Entrada 1  tiempo_carga      0 a 10 s   ->  Rápido | Moderado | Lento
    Entrada 2  errores_sintaxis  0 a 50     ->  Pocos  | Muchos
    Salida     mantenimiento     0 a 100    ->  Al día | Preventivo | Urgente
               (puntaje de necesidad de mantenimiento: 0 = nada, 100 = máxima)

¿Por qué lógica difusa? Porque "lento" no es un corte exacto: 2,9 s y 3,1 s
no deberían dar veredictos opuestos. Con conjuntos difusos un valor puede ser
"un poco Moderado y un poco Lento" a la vez, y el resultado cambia de forma
gradual.

Uso:
    from fuzzy.motor import evaluar
    r = evaluar(tiempo_carga=4.2, errores_sintaxis=12)
    r["nivel"]    -> 'Preventivo'
    r["puntaje"]  -> 50.0
"""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ---------------------------------------------------------------------------
# 1. Universos de discurso
# ---------------------------------------------------------------------------
TIEMPO_MAX = 10.0
ERRORES_MAX = 50.0

tiempo = ctrl.Antecedent(np.arange(0, TIEMPO_MAX + 0.01, 0.1), "tiempo_carga")
errores = ctrl.Antecedent(np.arange(0, ERRORES_MAX + 1, 1), "errores_sintaxis")
mantenimiento = ctrl.Consequent(np.arange(0, 101, 1), "mantenimiento")

# ---------------------------------------------------------------------------
# 2. Conjuntos difusos (funciones de pertenencia)
#    Los cortes se basan en referencias de la industria:
#    - Google considera "bueno" responder en menos de ~2-3 s; más de 5-6 s
#      hace que la mayoría de usuarios abandone la página.
#    - Unos pocos avisos del validador W3C son normales; decenas de errores
#      indican un HTML descuidado.
#    Los conjuntos se traslapan a propósito para que la transición sea suave.
# ---------------------------------------------------------------------------
tiempo["Rápido"] = fuzz.trapmf(tiempo.universe, [0, 0, 1.5, 3])
tiempo["Moderado"] = fuzz.trimf(tiempo.universe, [2, 4, 6])
tiempo["Lento"] = fuzz.trapmf(tiempo.universe, [5, 7, TIEMPO_MAX, TIEMPO_MAX])

errores["Pocos"] = fuzz.trapmf(errores.universe, [0, 0, 5, 20])
errores["Muchos"] = fuzz.trapmf(errores.universe, [10, 30, ERRORES_MAX, ERRORES_MAX])

mantenimiento["Al día"] = fuzz.trapmf(mantenimiento.universe, [0, 0, 20, 40])
mantenimiento["Preventivo"] = fuzz.trimf(mantenimiento.universe, [30, 50, 70])
mantenimiento["Urgente"] = fuzz.trapmf(mantenimiento.universe, [60, 80, 100, 100])

# ---------------------------------------------------------------------------
# 3. Base de reglas: cubre las 3 x 2 = 6 combinaciones posibles, así ningún
#    sitio queda sin veredicto. Cada regla tiene su justificación.
# ---------------------------------------------------------------------------
REGLAS = [
    # (tiempo, errores, salida, justificación)
    ("Rápido", "Pocos", "Al día",
     "Carga rápido y el código está limpio: solo requiere revisiones periódicas."),
    ("Rápido", "Muchos", "Preventivo",
     "Carga bien, pero los errores de código pueden romper la página en algunos navegadores."),
    ("Moderado", "Pocos", "Preventivo",
     "El código está bien, pero la velocidad ya está en el límite de lo que toleran los usuarios."),
    ("Moderado", "Muchos", "Urgente",
     "Velocidad en el límite y código con muchos errores: los problemas se suman."),
    ("Lento", "Pocos", "Urgente",
     "Aunque el código esté bien, una página lenta pierde a la mayoría de sus visitantes."),
    ("Lento", "Muchos", "Urgente",
     "Si el tiempo es Lento Y hay Muchos errores, el mantenimiento es Urgente (regla del enunciado)."),
]

_reglas_ctrl = [
    ctrl.Rule(tiempo[t] & errores[e], mantenimiento[s], label=f"R{i}")
    for i, (t, e, s, _) in enumerate(REGLAS, start=1)
]
_sistema = ctrl.ControlSystem(_reglas_ctrl)


def _pertenencias(variable, valor) -> dict:
    """Grado (0 a 1) en que 'valor' pertenece a cada conjunto de la variable."""
    return {
        nombre: round(float(fuzz.interp_membership(variable.universe, termino.mf, valor)), 3)
        for nombre, termino in variable.terms.items()
    }


def evaluar(tiempo_carga: float, errores_sintaxis: float) -> dict:
    """
    Ejecuta la inferencia difusa (Mamdani, defuzzificación por centroide).

    Devuelve un diccionario con:
      - puntaje: necesidad de mantenimiento de 0 a 100
      - nivel: 'Al día' | 'Preventivo' | 'Urgente' (conjunto de salida con mayor pertenencia)
      - entradas: valores usados (recortados al universo)
      - pertenencias: cómo se interpretó cada entrada, p. ej. {'Rápido': 0, 'Moderado': 0.9, ...}
      - reglas_activadas: reglas que se dispararon, con su fuerza y justificación
    """
    # Los valores fuera de rango se recortan: 25 s de carga sigue siendo "Lento".
    t = float(np.clip(tiempo_carga, 0, TIEMPO_MAX))
    e = float(np.clip(errores_sintaxis, 0, ERRORES_MAX))

    sim = ctrl.ControlSystemSimulation(_sistema)  # una simulación por llamada: seguro con varios agentes
    sim.input["tiempo_carga"] = t
    sim.input["errores_sintaxis"] = e
    sim.compute()
    puntaje = round(float(sim.output["mantenimiento"]), 1)

    pert_t = _pertenencias(tiempo, t)
    pert_e = _pertenencias(errores, e)
    pert_s = _pertenencias(mantenimiento, puntaje)
    nivel = max(pert_s, key=pert_s.get)

    activadas = []
    for i, (ct, ce, cs, por_que) in enumerate(REGLAS, start=1):
        fuerza = min(pert_t[ct], pert_e[ce])  # operador Y = mínimo
        if fuerza > 0:
            activadas.append({
                "regla": f"R{i}",
                "texto": f"SI el tiempo es {ct} Y los errores son {ce} ENTONCES el mantenimiento es {cs}",
                "fuerza": round(fuerza, 3),
                "justificacion": por_que,
            })
    activadas.sort(key=lambda r: -r["fuerza"])

    return {
        "puntaje": puntaje,
        "nivel": nivel,
        "entradas": {"tiempo_carga": t, "errores_sintaxis": e},
        "pertenencias": {
            "tiempo_carga": pert_t,
            "errores_sintaxis": pert_e,
            "mantenimiento": pert_s,
        },
        "reglas_activadas": activadas,
    }


def describir(resultado: dict) -> str:
    """Explicación corta en lenguaje natural del veredicto (para logs y Dashboard)."""
    def etiqueta(p):
        nombre = max(p, key=p.get)
        return f"{nombre} ({p[nombre]:.0%})"

    pt = resultado["pertenencias"]["tiempo_carga"]
    pe = resultado["pertenencias"]["errores_sintaxis"]
    ent = resultado["entradas"]
    return (
        f"Tiempo de carga {ent['tiempo_carga']:g} s = {etiqueta(pt)}; "
        f"{ent['errores_sintaxis']:g} errores = {etiqueta(pe)}. "
        f"Necesidad de mantenimiento: {resultado['puntaje']:g}/100 -> {resultado['nivel']}."
    )


if __name__ == "__main__":
    casos = [(0.8, 2), (1.2, 35), (3.5, 4), (4.2, 12), (4.0, 40), (7.5, 3), (9.0, 45), (2.9, 8), (3.1, 8)]
    print(f"{'tiempo':>7} {'errores':>8} {'puntaje':>8}  nivel")
    for t, e in casos:
        r = evaluar(t, e)
        print(f"{t:>6}s {e:>8} {r['puntaje']:>8}  {r['nivel']}")
    print()
    print(describir(evaluar(4.2, 12)))
