"""
Fase 4: convierte el informe del Agente Notificador en un documento JSON-LD
(Linked Data). No es un JSON plano: el @context dice qué significa cada campo,
usando schema.org (vocabulario controlado) y la ontología del proyecto (mw:).

Así cualquier sistema semántico puede leer los registros de MongoDB y saber,
por ejemplo, que "status" es mw:tieneEstado y que su valor es el individuo
mw:Critico de la ontología.

Estructura (sigue el ejemplo del enunciado, con significado formal):

{
  "@context": {...},
  "@id": "urn:uuid:...",
  "@type": ["Report", "mw:InformeAuditoria"],
  "site":   {"@id": "https://ejemplo.com", "@type": ["WebSite", "mw:SitioWeb"], "status": "mw:Critico", ...},
  "result": {"status": "Necesita mantenimiento urgente", "priority": "Alta", "tags": ["SEO", "Accesibilidad"]},
  "level": "mw:Urgente",
  "recommendations": ["mw:RecTextoAlternativo", ...],
  ...
}
"""
from ontologia.consultas import MW

NS_MW = str(MW)

# Nombres de individuos de la ontología para cada nivel / estado
NIVEL_A_IRI = {"Urgente": "mw:Urgente", "Preventivo": "mw:Preventivo", "Al día": "mw:AlDia"}
ESTADO_A_IRI = {"Crítico": "mw:Critico", "Aceptable": "mw:Aceptable", "Excelente": "mw:Excelente"}
NIVEL_A_PRIORIDAD = {"Urgente": "Alta", "Preventivo": "Media", "Al día": "Baja"}
NIVEL_A_TEXTO = {"Urgente": "Necesita mantenimiento urgente",
                 "Preventivo": "Necesita mantenimiento preventivo",
                 "Al día": "Al día"}

CONTEXTO = {
    "@vocab": "http://schema.org/",
    "mw": NS_MW,
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "_id": None,  # campo interno de MongoDB: no forma parte del grafo
    # Informe
    "site": {"@id": "mw:analizaSitio", "@type": "@id"},
    "level": {"@id": "mw:tieneNivel", "@type": "@id"},
    "fuzzyLevel": {"@id": "mw:tieneNivelDifuso", "@type": "@id"},
    "score": {"@id": "mw:puntajeDifuso", "@type": "xsd:decimal"},
    "recommendations": {"@id": "mw:incluyeRecomendacion", "@type": "@id"},
    "detail": {"@id": "mw:detalle", "@type": "@json"},
    "dateCreated": {"@id": "dateCreated", "@type": "xsd:dateTime"},
    # Resumen (campos del ejemplo del enunciado)
    "result": "mw:resultado",
    "status": {"@id": "mw:estadoTexto"},
    "priority": "mw:prioridad",
    "tags": "keywords",
    # Sitio
    "state": {"@id": "mw:tieneEstado", "@type": "@id"},
    "problems": {"@id": "mw:presentaProblema", "@type": "@id"},
    "url": {"@id": "url", "@type": "@id"},
}


def construir_jsonld(informe: dict) -> dict:
    """informe: lo que produce agentes.agente_notificador.estructurar_informe()."""
    d = informe["diagnostico"]
    m = informe["metricas"]
    url = m.get("url_final") or informe["sitio"]
    return {
        "@context": CONTEXTO,
        "@id": f"urn:uuid:{informe['id']}",
        "@type": ["Report", "mw:InformeAuditoria"],
        "name": f"Informe de mantenimiento de {informe['sitio']}",
        "dateCreated": informe["fecha"],
        "creator": {"@type": "SoftwareApplication", "name": "SEM-Web-Advisor"},
        "site": {
            "@id": url,
            "@type": ["WebSite", "mw:SitioWeb"],
            "url": url,
            "state": ESTADO_A_IRI[d["estado"]],
            "problems": [f"mw:{r['problema']}" for r in d["recomendaciones"]],
        },
        "result": {
            "status": NIVEL_A_TEXTO[d["nivel"]],
            "priority": NIVEL_A_PRIORIDAD[d["nivel"]],
            "tags": d["areas_afectadas"],
        },
        "level": NIVEL_A_IRI[d["nivel"]],
        "fuzzyLevel": NIVEL_A_IRI[d["nivel_difuso"]],
        "score": d["puntaje"],
        "recommendations": [f"mw:{r['recomendacion']}" for r in d["recomendaciones"]],
        "description": d["mensaje"],
        # Todo el detalle técnico se conserva para el Dashboard como literal rdf:JSON
        "detail": {"metricas": m, "diagnostico": d, "conversacion": informe.get("conversacion")},
    }


def a_grafo(documento: dict):
    """Interpreta el documento como RDF (prueba de que es Linked Data válido)."""
    import json

    from rdflib import Graph

    g = Graph()
    doc = {k: v for k, v in documento.items() if k != "_id"}
    g.parse(data=json.dumps(doc, ensure_ascii=False, default=str), format="json-ld")
    return g
