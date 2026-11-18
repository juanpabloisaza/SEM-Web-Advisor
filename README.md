# SEM-Web-Advisor

**Sistema Inteligente de Mantenimiento Web Semántico**
Proyecto Final — Web Semántica y Agentes Inteligentes (ING01243)
Politécnico Colombiano Jaime Isaza Cadavid · 2026-2 · Prof. Manolo Pájaro Borrás

Entrega: **10/12/2026** (25% de la materia)

## ¿Qué hace?

Analiza una página web y le dice al usuario, en lenguaje sencillo, qué mantenimiento necesita
(SEO, accesibilidad, rendimiento) y **por qué**, combinando lógica difusa, una ontología OWL
y un sistema de tres agentes que se comunican por mensajes ACL.

```
Dashboard (Flask) ──URL──► [Agente Analista] ──ACL──► [Agente Experto] ──ACL──► [Agente Notificador]
                            descarga el HTML,          lógica difusa +           informe JSON-LD
                            mide tiempo y errores      SPARQL a la ontología     → MongoDB
```

## Estructura del repositorio

| Carpeta | Fase | Contenido |
|---|---|---|
| `ontologia/` | 1 — Ontología | `mantenimiento_web.owl` (Protégé, RDF/XML) y consultas SPARQL |
| `fuzzy/` | 2 — Lógica difusa | Motor scikit-fuzzy y gráficas de funciones de pertenencia |
| `agentes/` | 3 — Multiagentes | Agentes SPADE: Analista, Experto, Notificador |
| `persistencia/` | 4 — MongoDB + JSON-LD | Conexión a MongoDB y construcción del informe Linked Data |
| `web/` | 5 — Interfaz | Dashboard en Flask |
| `docs/` | — | Documento del proyecto, guion del video, capturas |

## Requisitos

- Python 3.12
- MongoDB Community Server (local, puerto 27017)
- Protégé 5.6 (para abrir/editar la ontología)

En Windows se pueden instalar con `winget`:

```bash
winget install -e --id Python.Python.3.12
winget install -e --id MongoDB.Server
winget install -e --id MongoDB.Compass.Full
winget install -e --id Stanford.Protege
```

## Instalación

```bash
git clone https://github.com/juanpabloisaza/SEM-Web-Advisor.git
cd SEM-Web-Advisor
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> SPADE trae su propio servidor XMPP embebido, no hay que instalar Openfire ni Prosody.

## Ejecución

_Se completará a medida que avancen las fases._

## Integrantes

| Nombre | Usuario GitHub | Responsable de |
|---|---|---|
| | | |
| | | |
| | | |

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para la forma de trabajar en equipo.
