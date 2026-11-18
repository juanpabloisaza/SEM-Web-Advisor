# Fase 3: Sistema multiagente (20%)

Tres agentes **SPADE 4** autónomos que se comunican solo por mensajes **FIPA-ACL**, más un
agente puente (`AgenteInterfaz`) que representa al usuario. SPADE trae su propio servidor
XMPP embebido, así que no hay que instalar Openfire ni Prosody.

| Agente | Archivo | Qué hace |
|---|---|---|
| **Analista** (scraper) | [agente_analista.py](agente_analista.py) | Lee el HTML de la URL y mide el tiempo de respuesta, las imágenes sin `alt`, los errores de sintaxis, el título, la meta descripción, el idioma, los h1, los enlaces sin texto y el peso |
| **Experto** (Fuzzy-Onto) | [agente_experto.py](agente_experto.py) | Aplica la lógica difusa (Fase 2) y consulta la ontología con SPARQL (Fase 1) para elegir recomendaciones |
| **Notificador** (DB) | [agente_notificador.py](agente_notificador.py) | Estructura el informe final, lo guarda y avisa al solicitante |
| Interfaz (puente) | [sistema.py](sistema.py) | Envía la solicitud del usuario y espera la respuesta (lo usará el Dashboard) |

## Conversación (protocolo FIPA-Request)

Todos los mensajes llevan `ontology=mantenimiento_web`, `language=json`, `protocol=fipa-request`
y el mismo `thread`, que es el id de la conversación.

```
interfaz ──request(url)───────────► analista
analista ──agree──────────────────► interfaz        acepta la tarea
analista ──inform(métricas)───────► experto
experto  ──inform(diagnóstico)────► notificador
notificador ──inform(informe)─────► interfaz        fin
           o bien
analista ──refuse─────────────────► interfaz        robots.txt no lo permite
analista ──failure────────────────► interfaz        el sitio no responde / URL inválida
```

Ejemplo real (`python -m agentes.sistema https://www.politecnicojic.edu.co`):

```
interfaz    -> analista    request  analizar https://www.politecnicojic.edu.co
analista    -> interfaz    agree    acepto analizar https://www.politecnicojic.edu.co
analista    -> experto     inform   0.92 s, 3 errores, 1 imágenes sin alt
experto     -> notificador inform   nivel Preventivo (15.6/100), 2 recomendaciones
notificador -> interfaz    inform   informe 2094ec42 guardado
```

## Arquitectura BDI (simplificada)

Cada agente documenta en su código sus **Creencias** (`self.creencias`), sus **Deseos**
(objetivo) y sus **Intenciones** (plan de pasos), como en el taller de agentes.

| Agente | Creencias | Deseos | Intenciones |
|---|---|---|---|
| Analista | Última URL y métricas, análisis realizados | Que cada URL quede medida | Revisar robots.txt → medir → informar al Experto |
| Experto | Ontología cargada (≈540 tripletas), diagnósticos emitidos | Que el dueño sepa qué hacer | Lógica difusa → SPARQL → combinar → informar |
| Notificador | Informes guardados, último id | Que ningún diagnóstico se pierda | Estructurar → guardar → avisar al solicitante |

## Razonamiento del Experto: combinar lógica difusa y ontología

La lógica difusa del enunciado solo considera velocidad y errores de sintaxis. Si la ontología
detecta problemas de **prioridad Alta**, como imágenes sin texto alternativo, el Experto no
permite el veredicto «Al día» y lo sube a «Preventivo». El informe guarda los dos valores
(`nivel_difuso` y `nivel`) y el motivo (`ajuste_semantico`) para que el Dashboard lo explique.
El veredicto difuso nunca se baja.

## Ética y privacidad

- El Analista **respeta robots.txt**: si el sitio no permite robots en esa ruta, responde `refuse`.
- Hace una sola petición a la página pública solicitada, sin seguir enlaces.
- Se identifica con un User-Agent propio (`SEM-Web-Advisor/1.0 (proyecto academico…)`).
- No guarda el HTML ni datos personales, solo métricas numéricas.

## Errores de sintaxis

Se cuentan con **html5lib**, que aplica el algoritmo de análisis del estándar HTML5, el mismo de
los navegadores. Se ignora `invalid-codepoint`, porque html5lib lo reporta con caracteres
Unicode válidos (emojis, otros alfabetos): Wikipedia pasaba de 875 «errores» a 5 reales.

## Uso

```bash
python -m agentes.sistema https://example.com https://www.wikipedia.org
python -m agentes.analizador https://example.com     # solo las métricas, sin agentes
python -m unittest discover tests                    # incluye prueba de extremo a extremo
```

En esta fase el Notificador guarda los informes en memoria. En la **Fase 4** se le pasa la
función que los guarda en MongoDB como JSON-LD (`SistemaMultiagente(guardar=...)`).
