"""Configuración compartida por los agentes."""

# Servidor XMPP: SPADE trae uno embebido (spade.run(..., embedded_xmpp_server=True)).
SERVIDOR_XMPP = "localhost"
CLAVE_AGENTES = "sem-web-advisor"  # solo para el servidor local embebido

JID_ANALISTA = f"analista@{SERVIDOR_XMPP}"
JID_EXPERTO = f"experto@{SERVIDOR_XMPP}"
JID_NOTIFICADOR = f"notificador@{SERVIDOR_XMPP}"
JID_INTERFAZ = f"interfaz@{SERVIDOR_XMPP}"

# Metadatos FIPA-ACL comunes a todos los mensajes del sistema
ONTOLOGIA = "mantenimiento_web"  # nombre de la ontología compartida (Fase 1)
LENGUAJE = "json"
PROTOCOLO = "fipa-request"

# Analista
USER_AGENT = "SEM-Web-Advisor/1.0 (proyecto academico; analisis de mantenimiento web)"
TIEMPO_ESPERA_HTTP = 15  # segundos
