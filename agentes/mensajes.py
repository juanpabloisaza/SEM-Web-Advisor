"""
Utilidades de comunicación FIPA-ACL compartidas por los agentes.

Cada mensaje lleva los metadatos estándar de FIPA-ACL:
  performative  request | inform | agree | refuse | failure
  ontology      mantenimiento_web  (todos los agentes comparten la ontología de la Fase 1)
  language      json               (el contenido viaja como JSON)
  protocol      fipa-request
  thread        id de conversación  (agrupa todos los mensajes de un mismo análisis)

Además se lleva un registro de todos los mensajes enviados (registro_acl) que el
Dashboard muestra como "conversación entre agentes".
"""
import json
import logging
from collections import deque
from datetime import datetime

from spade.message import Message
from spade.template import Template

from agentes.config import LENGUAJE, ONTOLOGIA, PROTOCOLO

log = logging.getLogger("sem-web-advisor")

# Últimos mensajes intercambiados (para mostrarlos en la interfaz)
registro_acl: deque = deque(maxlen=200)


def crear_mensaje(para: str, performativa: str, contenido: dict, conversacion: str) -> Message:
    msg = Message(to=para)
    msg.thread = conversacion
    msg.set_metadata("performative", performativa)
    msg.set_metadata("ontology", ONTOLOGIA)
    msg.set_metadata("language", LENGUAJE)
    msg.set_metadata("protocol", PROTOCOLO)
    msg.body = json.dumps(contenido, ensure_ascii=False)
    return msg


async def enviar(comportamiento, msg: Message, resumen: str = "") -> None:
    """Envía un mensaje y lo deja en el registro."""
    await comportamiento.send(msg)
    origen = str(comportamiento.agent.jid).split("@")[0]
    destino = str(msg.to).split("@")[0]
    performativa = msg.get_metadata("performative")
    registro_acl.append({
        "hora": datetime.now().strftime("%H:%M:%S"),
        "conversacion": msg.thread,
        "de": origen,
        "para": destino,
        "performativa": performativa,
        "resumen": resumen,
    })
    log.info("[%s -> %s] %s: %s", origen, destino, performativa, resumen)


def leer(msg: Message) -> dict:
    return json.loads(msg.body) if msg and msg.body else {}


def plantilla(performativa: str) -> Template:
    """Filtro para que un comportamiento solo reciba cierto tipo de mensajes."""
    t = Template()
    t.set_metadata("performative", performativa)
    t.set_metadata("ontology", ONTOLOGIA)
    return t
