"""
Agente 2: EXPERTO (Fuzzy-Onto)

Recibe las métricas del Analista, aplica la lógica difusa (Fase 2) y consulta
la ontología con SPARQL (Fase 1) para decidir qué recomendaciones dar. Envía
el diagnóstico al Agente Notificador.

Arquitectura BDI simplificada:
  Creencias   -> el conocimiento de la ontología (problemas, umbrales, recomendaciones)
                 + las métricas recibidas.
  Deseos      -> que el dueño del sitio sepa qué tan urgente es el mantenimiento y qué hacer.
  Intenciones -> plan: (1) inferir el nivel con lógica difusa, (2) traducirlo a un estado
                 con la ontología, (3) seleccionar recomendaciones con SPARQL, (4) informar.
"""
import asyncio

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from agentes.config import JID_NOTIFICADOR
from agentes.mensajes import crear_mensaje, enviar, leer, plantilla
from fuzzy.motor import describir, evaluar
from ontologia.consultas import cargar_grafo, interpretar_nivel, recomendaciones_para


ORDEN_NIVELES = ["Al día", "Preventivo", "Urgente"]


def diagnosticar(metricas: dict) -> dict:
    """Razonamiento del Experto (separado del agente para poder probarlo solo)."""
    # (1) Lógica difusa: datos numéricos -> término lingüístico
    difuso = evaluar(metricas["tiempo_carga"], metricas["errores_sintaxis"])
    # (2) Ontología (SPARQL): métricas -> problemas detectados -> recomendaciones
    recomendaciones = recomendaciones_para(metricas)
    areas = sorted({a for r in recomendaciones for a in r["areas"]})

    # (3) Combinar ambas fuentes. La lógica difusa solo mira velocidad y errores de
    #     sintaxis; si la ontología encontró problemas de prioridad Alta (p. ej. imágenes
    #     sin texto alternativo), decir "Al día" sería contradictorio. En ese caso el
    #     nivel sube a Preventivo. Nunca se baja el veredicto difuso.
    nivel = difuso["nivel"]
    ajuste = None
    altas = [r["titulo"] for r in recomendaciones if r["prioridad"] == "Alta"]
    if altas and ORDEN_NIVELES.index(nivel) < ORDEN_NIVELES.index("Preventivo"):
        nivel = "Preventivo"
        ajuste = (f"La lógica difusa indicó «{difuso['nivel']}» por velocidad y errores, pero la "
                  f"ontología detectó {len(altas)} problema(s) de prioridad Alta "
                  f"({'; '.join(altas)}), así que el nivel sube a «Preventivo».")

    # (4) Ontología: nivel -> estado del sitio + mensaje para el usuario
    interpretacion = interpretar_nivel(nivel)
    return {
        "nivel": nivel,
        "nivel_difuso": difuso["nivel"],
        "ajuste_semantico": ajuste,
        "puntaje": difuso["puntaje"],
        "explicacion_difusa": describir(difuso),
        "reglas_activadas": difuso["reglas_activadas"],
        "pertenencias": difuso["pertenencias"],
        "estado": interpretacion["estado"],
        "mensaje": interpretacion["mensaje"],
        "explicacion_estado": interpretacion["explicacion_estado"],
        "areas_afectadas": areas,
        "recomendaciones": recomendaciones,
    }


class AgenteExperto(Agent):

    class Diagnosticar(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return
            datos = leer(msg)
            metricas = datos["metricas"]

            diagnostico = await asyncio.to_thread(diagnosticar, metricas)
            self.agent.creencias["diagnosticos_emitidos"] += 1

            contenido = {"solicitante": datos["solicitante"], "metricas": metricas, "diagnostico": diagnostico}
            await enviar(self, crear_mensaje(JID_NOTIFICADOR, "inform", contenido, msg.thread),
                         f"nivel {diagnostico['nivel']} ({diagnostico['puntaje']}/100), "
                         f"{len(diagnostico['recomendaciones'])} recomendaciones")

    async def setup(self):
        # Creencia inicial: cargar la ontología una vez al nacer el agente
        grafo = await asyncio.to_thread(cargar_grafo)
        self.creencias = {"tripletas_ontologia": len(grafo), "diagnosticos_emitidos": 0}
        self.add_behaviour(self.Diagnosticar(), plantilla("inform"))
