"""
Ejecuta el sistema multiagente (SPADE + servidor XMPP embebido) en un hilo de
fondo, para que Flask pueda enviarle análisis sin bloquearse.

Flask (hilo principal) ──lanzar(url)──► loop asyncio de SPADE (hilo de fondo)
                         ◄─estado/ACL──  (registro_acl + diccionario de trabajos)
"""
import asyncio
import signal
import threading
import time
import uuid

import spade

# El servidor XMPP embebido (pyjabber) registra un manejador de Ctrl+C con
# signal.signal(), que Python solo permite en el hilo principal. Como aquí los
# agentes viven en un hilo de fondo, esa llamada se ignora fuera del hilo
# principal (Ctrl+C lo sigue atendiendo Flask, que sí está en el principal).
_signal_original = signal.signal


def _signal_solo_hilo_principal(numero, manejador):
    if threading.current_thread() is threading.main_thread():
        return _signal_original(numero, manejador)
    return None


signal.signal = _signal_solo_hilo_principal

from agentes.mensajes import registro_acl
from agentes.sistema import ErrorAnalisis, SistemaMultiagente


class RuntimeAgentes:

    def __init__(self, repositorio):
        self.repo = repositorio
        self.loop: asyncio.AbstractEventLoop | None = None
        self.sistema: SistemaMultiagente | None = None
        self.trabajos: dict[str, dict] = {}
        self._listo = threading.Event()
        self._parar: asyncio.Event | None = None
        self._error: BaseException | None = None

    # ---------------- ciclo de vida ----------------
    def iniciar(self, espera: float = 30):
        threading.Thread(target=self._hilo, name="spade", daemon=True).start()
        if not self._listo.wait(espera):
            raise RuntimeError("Los agentes no arrancaron a tiempo")
        if self._error:
            raise RuntimeError(f"Error al arrancar los agentes: {self._error}")

    def _hilo(self):
        spade.run(self._vivir(), embedded_xmpp_server=True)

    async def _vivir(self):
        try:
            self.loop = asyncio.get_running_loop()
            self._parar = asyncio.Event()
            self.sistema = SistemaMultiagente(guardar=self.repo.guardar)
            await self.sistema.iniciar()
        except BaseException as e:  # noqa: BLE001
            self._error = e
            self._listo.set()
            raise
        self._listo.set()
        await self._parar.wait()
        await self.sistema.detener()

    def detener(self):
        if self.loop and self._parar:
            self.loop.call_soon_threadsafe(self._parar.set)

    # ---------------- análisis ----------------
    def lanzar(self, url: str) -> str:
        """Inicia un análisis y devuelve el id de conversación ACL para consultar su avance."""
        conv = str(uuid.uuid4())
        self.trabajos[conv] = {"conversacion": conv, "url": url, "estado": "en_proceso",
                               "inicio": time.time(), "informe_id": None, "error": None}
        futuro = asyncio.run_coroutine_threadsafe(self.sistema.analizar(url, 60, conv), self.loop)
        futuro.add_done_callback(lambda f: self._terminar(conv, f))
        return conv

    def _terminar(self, conv, futuro):
        trabajo = self.trabajos[conv]
        try:
            respuesta = futuro.result()
            trabajo["informe_id"] = respuesta["id"]
            self.repo.agregar_conversacion(respuesta["id"], self.mensajes(conv))
            trabajo["estado"] = "listo"
        except ErrorAnalisis as e:
            trabajo.update(estado="error", error=str(e))
        except Exception as e:  # noqa: BLE001
            trabajo.update(estado="error", error=f"Error inesperado: {e}")
        trabajo["duracion"] = round(time.time() - trabajo["inicio"], 2)

    def estado(self, conv: str) -> dict | None:
        trabajo = self.trabajos.get(conv)
        if trabajo is None:
            return None
        return {**trabajo, "mensajes": self.mensajes(conv)}

    @staticmethod
    def mensajes(conv: str) -> list[dict]:
        return [m for m in list(registro_acl) if m["conversacion"] == conv]

    def creencias(self) -> dict:
        if not self.sistema:
            return {}
        return {
            "analista": dict(self.sistema.analista.creencias, ultimas_metricas=None),
            "experto": self.sistema.experto.creencias,
            "notificador": self.sistema.notificador.creencias,
        }
