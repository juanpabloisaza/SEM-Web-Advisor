# Fase 4: Persistencia semántica, MongoDB + JSON-LD (20%)

El Agente Notificador guarda cada informe en **MongoDB** (base `sem_web_advisor`, colección
`informes`) como un documento **JSON-LD**. No es un JSON plano: incluye su `@context`, así que
cualquier sistema semántico puede leerlo como RDF y saber qué significa cada campo.

| Archivo | Contenido |
|---|---|
| [jsonld.py](jsonld.py) | `construir_jsonld(informe)`: arma el documento Linked Data. `a_grafo(doc)`: lo convierte a RDF |
| [repositorio.py](repositorio.py) | `RepositorioInformes`: guardar, obtener, listar, estadísticas y grafo RDF de todos los informes |
| [../docs/ejemplo_informe.jsonld](../docs/ejemplo_informe.jsonld) | Informe real guardado tras analizar politecnicojic.edu.co |

## Estructura del documento

Sigue el ejemplo del enunciado (`site`, `result.status`, `result.priority`, `result.tags`), pero
cada campo está definido en el `@context`:

```json
{
  "@context": {
    "@vocab": "http://schema.org/",
    "mw": "http://www.semanticweb.org/sem-web-advisor/mantenimiento_web#",
    "site":   {"@id": "mw:analizaSitio",  "@type": "@id"},
    "state":  {"@id": "mw:tieneEstado",   "@type": "@id"},
    "level":  {"@id": "mw:tieneNivel",    "@type": "@id"},
    "result": "mw:resultado",
    "status": "mw:estadoTexto",
    "priority": "mw:prioridad",
    "tags":   "keywords",
    "...": "..."
  },
  "@id": "urn:uuid:1dc2ea9a-…",
  "@type": ["Report", "mw:InformeAuditoria"],
  "site": {
    "@id": "https://www.politecnicojic.edu.co/",
    "@type": ["WebSite", "mw:SitioWeb"],
    "state": "mw:Aceptable",
    "problems": ["mw:ProblemaImagenesSinAlt", "mw:ProblemaEncabezadoIncorrecto"]
  },
  "result": {"status": "Necesita mantenimiento preventivo", "priority": "Media", "tags": ["Accesibilidad", "SEO"]},
  "level": "mw:Preventivo",
  "fuzzyLevel": "mw:AlDia",
  "score": 15.6,
  "recommendations": ["mw:RecTextoAlternativo", "mw:RecEncabezado"],
  "detail": { "metricas": {…}, "diagnostico": {…} }
}
```

### Decisiones

- **Vocabulario controlado:** los tipos y propiedades genéricas vienen de **schema.org**
  (`Report`, `WebSite`, `keywords`, `dateCreated`, `creator`). Lo propio del dominio viene de la
  **ontología del proyecto** (`mw:`). El enunciado usaba `"@type": "AuditReport"`, pero ese tipo no
  existe en schema.org, así que se usa `Report` junto con `mw:InformeAuditoria`.
- **Enlaces reales a la ontología:** el estado, el nivel, los problemas y las recomendaciones se
  guardan como IRIs de individuos de la ontología (`mw:Aceptable`, `mw:RecTextoAlternativo`…), no
  como texto. Una prueba automática verifica que **todas** las IRIs `mw:` del informe existan en
  la ontología.
- **`_id` de MongoDB:** el `@context` lo declara `null`, así que no entra al grafo RDF.
- **`detail`:** las métricas y el diagnóstico completos (reglas difusas activadas, pertenencias…)
  se guardan como literal `rdf:JSON` (`"@type": "@json"`, JSON-LD 1.1) para que el Dashboard los
  muestre sin perder la validez semántica del documento.
- La ontología se amplió con `mw:resultado`, `mw:estadoTexto`, `mw:puntajeDifuso`,
  `mw:tieneNivelDifuso` y `mw:detalle`. Sigue siendo consistente según HermiT.

## Prueba de que es Linked Data

`python -m persistencia.repositorio` lee los informes de MongoDB, los convierte a RDF, los une con
la ontología y ejecuta una consulta SPARQL. Los informes solo guardan IRIs, y el área de cada
recomendación sale de la ontología:

```
MongoDB 9.0.4 - 2 informes en sem_web_advisor.informes
Grafo RDF (informes + ontología): 614 tripletas
SPARQL: recomendaciones de cada sitio y su área, según la ontología
  https://example.com/  [Excelente]  SEO: Agregue una descripción para buscadores
  https://www.politecnicojic.edu.co/  [Aceptable]  Accesibilidad: Describa sus imágenes
  https://www.politecnicojic.edu.co/  [Aceptable]  SEO: Ordene los encabezados
```

## Uso

```bash
python -m agentes.sistema https://example.com   # analiza y guarda en MongoDB
python -m persistencia.repositorio              # lista informes + consulta SPARQL
python -m unittest discover tests               # las pruebas de Mongo usan la base sem_web_advisor_pruebas
```

Para ver los registros con interfaz gráfica: abrir **MongoDB Compass**, conectarse a
`mongodb://localhost:27017` y entrar a `sem_web_advisor` → `informes`.

Configuración opcional: variables de entorno `MONGO_URI` y `MONGO_DB`. Si MongoDB no está
corriendo, el sistema sigue funcionando y guarda en memoria, con un aviso.
