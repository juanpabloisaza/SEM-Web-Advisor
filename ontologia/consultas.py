"""
Consultas SPARQL sobre la ontología mantenimiento_web.owl.

Es el módulo que usa el Agente Experto para "consultar la ontología y decidir
qué recomendación dar". La decisión NO está escrita a mano en Python: los
problemas, sus umbrales y las recomendaciones viven en la ontología, y aquí
solo se consultan con SPARQL (rdflib).

Uso rápido (desde la raíz del repo):
    python -m ontologia.consultas
"""
from functools import lru_cache
from pathlib import Path

from rdflib import Graph, Literal, Namespace

RUTA_OWL = Path(__file__).with_name("mantenimiento_web.owl")
MW = Namespace("http://www.semanticweb.org/sem-web-advisor/mantenimiento_web#")

PREFIJOS = """
PREFIX mw:   <http://www.semanticweb.org/sem-web-advisor/mantenimiento_web#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# ---------------------------------------------------------------------------
# Consulta 1: catálogo de problemas detectables (métrica + umbral + área)
# El área (SEO / Accesibilidad / Rendimiento) se obtiene del TIPO de la
# práctica incumplida, que es subclase de BuenasPracticas.
# ---------------------------------------------------------------------------
Q_PROBLEMAS = PREFIJOS + """
SELECT ?problema ?nombre ?metrica ?umbral ?unidad ?gravedad
       ?rec ?titulo ?prioridad ?explicacion ?accion ?pasos
       (GROUP_CONCAT(DISTINCT ?area; separator=",") AS ?areas)
WHERE {
    ?problema a mw:Problema ;
              rdfs:label ?nombre ;
              mw:metrica ?metrica ;
              mw:umbral ?umbral ;
              mw:gravedad ?gravedad ;
              mw:incumplePractica ?practica .
    OPTIONAL { ?problema mw:unidad ?unidad }

    ?practica a ?claseArea .
    ?claseArea rdfs:subClassOf mw:BuenasPracticas ;
               rdfs:label ?area .

    ?rec mw:atiendeProblema ?problema ;
         rdfs:label ?titulo ;
         mw:prioridad ?prioridad ;
         mw:explicacion ?explicacion ;
         mw:sugiereAccion ?acc .
    ?acc rdfs:label ?accion ;
         mw:pasosSolucion ?pasos .
}
GROUP BY ?problema ?nombre ?metrica ?umbral ?unidad ?gravedad
         ?rec ?titulo ?prioridad ?explicacion ?accion ?pasos
ORDER BY DESC(?gravedad)
"""

# ---------------------------------------------------------------------------
# Consulta 2: qué significa un nivel de mantenimiento (salida difusa)
# ---------------------------------------------------------------------------
Q_NIVEL = PREFIJOS + """
SELECT ?nombreNivel ?mensaje ?nombreEstado ?explicacionEstado
WHERE {
    ?nivel a mw:NivelMantenimiento ;
           rdfs:label ?nombreNivel ;
           mw:mensaje ?mensaje ;
           mw:correspondeAEstado ?estado .
    ?estado rdfs:label ?nombreEstado ;
            mw:explicacion ?explicacionEstado .
}
"""


@lru_cache(maxsize=1)
def cargar_grafo() -> Graph:
    """Carga la ontología una sola vez (queda en caché)."""
    g = Graph()
    g.parse(RUTA_OWL, format="xml")
    return g


def _local(iri) -> str:
    return str(iri).split("#")[-1]


def catalogo_problemas() -> list[dict]:
    """Todos los problemas que la ontología sabe detectar, con su recomendación."""
    filas = cargar_grafo().query(Q_PROBLEMAS)
    return [
        {
            "problema": _local(f.problema),
            "nombre": str(f.nombre),
            "metrica": str(f.metrica),
            "umbral": float(f.umbral),
            "unidad": str(f.unidad) if f.unidad else "",
            "gravedad": int(f.gravedad),
            "areas": sorted(str(f.areas).split(",")),
            "recomendacion": _local(f.rec),
            "titulo": str(f.titulo),
            "prioridad": str(f.prioridad),
            "explicacion": str(f.explicacion),
            "accion": str(f.accion),
            "pasos": str(f.pasos),
        }
        for f in filas
    ]


def recomendaciones_para(metricas: dict) -> list[dict]:
    """
    Devuelve las recomendaciones que aplican a las métricas medidas por el Analista.

    Un problema existe si  valor_medido > umbral  (regla definida en la ontología,
    propiedad mw:umbral). Las métricas que no se midieron se ignoran.
    """
    orden = {"Alta": 0, "Media": 1, "Baja": 2}
    salida = []
    for p in catalogo_problemas():
        valor = metricas.get(p["metrica"])
        if valor is not None and float(valor) > p["umbral"]:
            salida.append({**p, "valor": valor})
    return sorted(salida, key=lambda r: (orden.get(r["prioridad"], 9), -r["gravedad"]))


def interpretar_nivel(nivel: str) -> dict:
    """
    Traduce el veredicto difuso ('Urgente', 'Preventivo', 'Al día') al estado
    del sitio y al mensaje para el usuario, según la ontología.
    """
    g = cargar_grafo()
    filas = g.query(Q_NIVEL)
    for f in filas:
        if str(f.nombreNivel).lower() == nivel.lower():
            return {
                "nivel": str(f.nombreNivel),
                "mensaje": str(f.mensaje),
                "estado": str(f.nombreEstado),
                "explicacion_estado": str(f.explicacionEstado),
            }
    raise ValueError(f"Nivel desconocido en la ontología: {nivel!r}")


if __name__ == "__main__":
    g = cargar_grafo()
    print(f"Ontología cargada: {len(g)} tripletas\n")

    print("Problemas que el sistema sabe detectar:")
    for p in catalogo_problemas():
        print(f"  - [{'/'.join(p['areas'])}] {p['nombre']}: {p['metrica']} > {p['umbral']:g} {p['unidad']}")

    ejemplo = {"tiempo_carga": 4.2, "imagenes_sin_alt": 7, "errores_sintaxis": 2,
               "sin_titulo": 0, "sin_meta_descripcion": 1, "sin_idioma": 0}
    print(f"\nEjemplo de métricas medidas: {ejemplo}")
    for r in recomendaciones_para(ejemplo):
        print(f"  [{r['prioridad']}] {r['titulo']} -> {r['accion']}")
        print(f"      Por qué: {r['explicacion']}")

    print()
    for n in ("Urgente", "Preventivo", "Al día"):
        i = interpretar_nivel(n)
        print(f"  {i['nivel']} -> estado {i['estado']}: {i['mensaje']}")
