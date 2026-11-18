"""
Agente 1: ANALISTA (scraper)

Recibe un REQUEST con una URL, lee su HTML y mide cuánto tarda el servidor,
cuántas imágenes no tienen alt, errores de sintaxis, etc. Envía las métricas
al Agente Experto con un INFORM.

Arquitectura BDI simplificada:
  Creencias   -> self.creencias: última URL analizada, sus métricas y cuántos análisis lleva.
  Deseos      -> que cada URL solicitada quede medida y llegue al Experto.
  Intenciones -> plan: (1) verificar robots.txt, (2) descargar y medir,
                 (3) informar al Experto; si no puede, informar el fallo al solicitante.

Conversación (protocolo FIPA-Request):
  interfaz --request(url)--> analista
  analista --agree--------> interfaz        (acepta la tarea)
  analista --inform(metricas)--> experto    (o refuse/failure --> interfaz)
"""
import asyncio

import requests
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from agentes.analizador import AnalisisNoPermitido, analizar_url
from agentes.config import JID_EXPERTO
from agentes.mensajes import crear_mensaje, enviar, leer, plantilla


def _motivo_legible(e: requests.RequestException) -> str:
    """Mensaje de error comprensible para una persona que no programa."""
    if isinstance(e, requests.Timeout):
        return "El sitio tardó demasiado en responder (más de 15 segundos)."
    if isinstance(e, requests.exceptions.SSLError):
        return "El certificado de seguridad (HTTPS) del sitio no es válido."
    if isinstance(e, requests.ConnectionError):
        return "No se pudo conectar con el sitio. Revise que la dirección esté bien escrita y que el sitio exista."
    return f"No se pudo leer la página ({type(e).__name__})."


class AgenteAnalista(Agent):

    class AtenderSolicitudes(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return
            datos = leer(msg)
            url = datos.get("url", "")
            solicitante = str(msg.sender)
            conv = msg.thread

            # Intención 1: aceptar la tarea (FIPA-Request: agree)
            await enviar(self, crear_mensaje(solicitante, "agree", {"url": url}, conv),
                         f"acepto analizar {url}")

            # Intención 2: percibir el entorno (la página web)
            try:
                # La descarga es bloqueante: se ejecuta en un hilo para no congelar al agente
                metricas = await asyncio.to_thread(analizar_url, url)
            except AnalisisNoPermitido as e:
                await enviar(self, crear_mensaje(solicitante, "refuse", {"url": url, "motivo": str(e)}, conv),
                             "robots.txt no lo permite")
                return
            except ValueError as e:
                await enviar(self, crear_mensaje(solicitante, "failure", {"url": url, "motivo": str(e)}, conv),
                             "URL no válida")
                return
            except requests.RequestException as e:
                motivo = _motivo_legible(e)
                await enviar(self, crear_mensaje(solicitante, "failure", {"url": url, "motivo": motivo}, conv),
                             f"no pude leer la página: {type(e).__name__}")
                return

            # Actualizar creencias
            self.agent.creencias.update(ultima_url=url, ultimas_metricas=metricas,
                                        analisis_realizados=self.agent.creencias["analisis_realizados"] + 1)

            # Intención 3: informar al Experto, indicando a quién responder al final
            contenido = {"solicitante": solicitante, "metricas": metricas}
            await enviar(self, crear_mensaje(JID_EXPERTO, "inform", contenido, conv),
                         f"{metricas['tiempo_carga']} s, {metricas['errores_sintaxis']} errores, "
                         f"{metricas['imagenes_sin_alt']} imágenes sin alt")

    async def setup(self):
        self.creencias = {"ultima_url": None, "ultimas_metricas": None, "analisis_realizados": 0}
        self.add_behaviour(self.AtenderSolicitudes(), plantilla("request"))
