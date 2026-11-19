"""
Agente 3: NOTIFICADOR (DB)

Recibe el diagnóstico del Experto, lo estructura como informe final, lo guarda
y avisa al solicitante original que el informe está listo.

Arquitectura BDI simplificada:
  Creencias   -> cuántos informes ha guardado y el id del último.
  Deseos      -> que ningún diagnóstico se pierda y que el usuario reciba su informe.
  Intenciones -> plan: (1) estructurar el informe, (2) guardarlo, (3) informar al solicitante.

El almacenamiento se recibe como parámetro (función `guardar(informe) -> id`):
en la Fase 4 se conecta MongoDB con formato JSON-LD.
"""
import asyncio
import uuid
from datetime import datetime, timezone

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

from agentes.mensajes import crear_mensaje, enviar, leer, plantilla


def estructurar_informe(metricas: dict, diagnostico: dict, conversacion: str | None = None) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sitio": metricas["url"],
        "conversacion": conversacion,  # thread ACL que produjo este informe
        "metricas": metricas,
        "diagnostico": diagnostico,
    }


def guardar_en_memoria(informe: dict) -> str:
    """Almacenamiento por defecto (sin base de datos), útil para pruebas."""
    guardar_en_memoria.informes.append(informe)
    return informe["id"]


guardar_en_memoria.informes = []


class AgenteNotificador(Agent):

    def __init__(self, *args, guardar=guardar_en_memoria, **kwargs):
        super().__init__(*args, **kwargs)
        self.guardar = guardar

    class GuardarYNotificar(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return
            datos = leer(msg)
            informe = estructurar_informe(datos["metricas"], datos["diagnostico"], msg.thread)
            try:
                id_guardado = await asyncio.to_thread(self.agent.guardar, informe)
            except Exception as e:  # p. ej. MongoDB apagado
                await enviar(self, crear_mensaje(datos["solicitante"], "failure",
                                                 {"motivo": f"No se pudo guardar el informe: {e}",
                                                  "informe": informe}, msg.thread),
                             "fallo al guardar")
                return

            self.agent.creencias["informes_guardados"] += 1
            self.agent.creencias["ultimo_id"] = id_guardado
            await enviar(self, crear_mensaje(datos["solicitante"], "inform",
                                             {"id": str(id_guardado), "informe": informe}, msg.thread),
                         f"informe {str(id_guardado)[:8]} guardado")

    async def setup(self):
        self.creencias = {"informes_guardados": 0, "ultimo_id": None}
        self.add_behaviour(self.GuardarYNotificar(), plantilla("inform"))
