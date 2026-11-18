"""
Arranque y orquestación del sistema multiagente.

Además de los 3 agentes del enunciado hay un agente puente, AgenteInterfaz,
que representa al usuario: envía la solicitud (REQUEST) al Analista y espera
la respuesta final del Notificador. Así el Dashboard (Fase 5) habla con los
agentes solo por mensajes ACL, igual que ellos entre sí.

Flujo completo de una conversación (mismo thread):

    interfaz ──request(url)──────────► analista
    analista ──agree─────────────────► interfaz
    analista ──inform(métricas)──────► experto
    experto  ──inform(diagnóstico)───► notificador
    notificador ──inform(informe)────► interfaz

Uso por consola (desde la raíz del repo):
    python -m agentes.sistema https://example.com
"""
import asyncio
import json
import logging
import sys
import uuid

import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template

from agentes.agente_analista import AgenteAnalista
from agentes.agente_experto import AgenteExperto
from agentes.agente_notificador import AgenteNotificador, guardar_en_memoria
from agentes.config import (CLAVE_AGENTES, JID_ANALISTA, JID_EXPERTO, JID_INTERFAZ,
                            JID_NOTIFICADOR, ONTOLOGIA)
from agentes.mensajes import crear_mensaje, enviar, leer, registro_acl


class ErrorAnalisis(Exception):
    """El análisis no se pudo completar (refuse / failure / tiempo agotado)."""


class AgenteInterfaz(Agent):
    """Puente entre el usuario (consola o Dashboard) y el sistema multiagente."""

    class EnviarSolicitud(OneShotBehaviour):
        def __init__(self, url, conversacion):
            super().__init__()
            self.url, self.conversacion = url, conversacion

        async def run(self):
            await enviar(self, crear_mensaje(JID_ANALISTA, "request", {"url": self.url}, self.conversacion),
                         f"analizar {self.url}")

    class RecibirRespuestas(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return
            performativa = msg.get_metadata("performative")
            futuro = self.agent.pendientes.get(msg.thread)
            if futuro is None or futuro.done() or performativa == "agree":
                return
            datos = leer(msg)
            if performativa == "inform":
                futuro.set_result(datos)
            else:  # refuse / failure
                futuro.set_exception(ErrorAnalisis(datos.get("motivo", performativa)))

    async def setup(self):
        self.pendientes: dict[str, asyncio.Future] = {}
        t = Template()
        t.set_metadata("ontology", ONTOLOGIA)
        self.add_behaviour(self.RecibirRespuestas(), t)

    async def solicitar(self, url: str, timeout: float = 60) -> dict:
        conversacion = str(uuid.uuid4())
        futuro = asyncio.get_running_loop().create_future()
        self.pendientes[conversacion] = futuro
        self.add_behaviour(self.EnviarSolicitud(url, conversacion))
        try:
            return await asyncio.wait_for(futuro, timeout)
        except asyncio.TimeoutError:
            raise ErrorAnalisis(f"Los agentes no respondieron en {timeout} s")
        finally:
            self.pendientes.pop(conversacion, None)


class SistemaMultiagente:
    """Crea, arranca y detiene los 4 agentes. Debe usarse dentro de spade.run(...)."""

    def __init__(self, guardar=guardar_en_memoria):
        self.analista = AgenteAnalista(JID_ANALISTA, CLAVE_AGENTES)
        self.experto = AgenteExperto(JID_EXPERTO, CLAVE_AGENTES)
        self.notificador = AgenteNotificador(JID_NOTIFICADOR, CLAVE_AGENTES, guardar=guardar)
        self.interfaz = AgenteInterfaz(JID_INTERFAZ, CLAVE_AGENTES)
        self._agentes = [self.analista, self.experto, self.notificador, self.interfaz]

    async def iniciar(self):
        for agente in self._agentes:
            await agente.start(auto_register=True)

    async def analizar(self, url: str, timeout: float = 60) -> dict:
        """Envía la URL al sistema y espera el informe final del Notificador."""
        return await self.interfaz.solicitar(url, timeout)

    async def detener(self):
        for agente in reversed(self._agentes):
            await agente.stop()


def almacenamiento_por_defecto():
    """MongoDB (JSON-LD) si está disponible; si no, memoria con un aviso."""
    from persistencia.repositorio import RepositorioInformes, disponible

    if disponible():
        repo = RepositorioInformes()
        repo.crear_indices()
        return repo.guardar, f"MongoDB ({repo.col.full_name})"
    return guardar_en_memoria, "memoria (MongoDB no disponible: los informes no se conservarán)"


async def _main(urls):
    guardar, destino = almacenamiento_por_defecto()
    print("Informes se guardan en:", destino)
    sistema = SistemaMultiagente(guardar=guardar)
    await sistema.iniciar()
    try:
        for url in urls:
            print(f"\n=== Analizando {url} ===")
            try:
                respuesta = await sistema.analizar(url)
            except ErrorAnalisis as e:
                print("No se pudo analizar:", e)
                continue
            d = respuesta["informe"]["diagnostico"]
            print(f"Informe id: {respuesta['id']}")
            print(f"Veredicto: {d['nivel']} ({d['puntaje']}/100) -> estado {d['estado']}")
            print(d["explicacion_difusa"])
            print(d["mensaje"])
            for r in d["recomendaciones"]:
                print(f"  [{r['prioridad']}] {r['titulo']} ({'/'.join(r['areas'])})")
        print("\n=== Conversación ACL ===")
        for m in registro_acl:
            print(f"{m['hora']}  {m['de']:>11} -> {m['para']:<11} {m['performativa']:<8} {m['resumen']}")
    finally:
        await sistema.detener()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    spade.run(_main(sys.argv[1:] or ["https://example.com"]), embedded_xmpp_server=True)
