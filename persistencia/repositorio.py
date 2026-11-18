"""
Fase 4: repositorio de informes en MongoDB.

Cada informe se guarda TAL CUAL como documento JSON-LD (con su @context), de modo
que lo que hay en la base de datos ya es Linked Data. MongoDB solo agrega su campo
_id, que el @context declara como nulo (no entra al grafo RDF).

Configuración por variables de entorno (opcional):
    MONGO_URI  (por defecto mongodb://localhost:27017)
    MONGO_DB   (por defecto sem_web_advisor)

Uso por consola:
    python -m persistencia.repositorio          # lista los últimos informes
"""
import os

from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from persistencia.jsonld import a_grafo, construir_jsonld

URI_POR_DEFECTO = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
BD_POR_DEFECTO = os.environ.get("MONGO_DB", "sem_web_advisor")


class RepositorioInformes:

    def __init__(self, uri: str = URI_POR_DEFECTO, base_datos: str = BD_POR_DEFECTO,
                 coleccion: str = "informes"):
        self.cliente = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.col = self.cliente[base_datos][coleccion]

    def verificar_conexion(self) -> str:
        """Lanza PyMongoError si MongoDB no está disponible; devuelve la versión."""
        return self.cliente.server_info()["version"]

    def crear_indices(self):
        self.col.create_index([("dateCreated", DESCENDING)])
        self.col.create_index("site.@id")
        self.col.create_index("level")

    def guardar(self, informe: dict) -> str:
        """Firma que espera el Agente Notificador: recibe el informe y devuelve su id."""
        documento = construir_jsonld(informe)
        documento["_id"] = informe["id"]
        self.col.insert_one(documento)
        return informe["id"]

    def obtener(self, id_informe: str) -> dict | None:
        return self.col.find_one({"_id": id_informe})

    def listar(self, limite: int = 20, sitio: str | None = None) -> list[dict]:
        filtro = {"site.@id": {"$regex": sitio, "$options": "i"}} if sitio else {}
        return list(self.col.find(filtro).sort("dateCreated", DESCENDING).limit(limite))

    def contar(self) -> int:
        return self.col.count_documents({})

    def estadisticas(self) -> dict:
        """Cantidad de informes por nivel (para el Dashboard)."""
        return {d["_id"]: d["n"] for d in self.col.aggregate([{"$group": {"_id": "$level", "n": {"$sum": 1}}}])}

    def grafo(self, limite: int = 1000):
        """Une todos los informes en un solo grafo RDF (para consultarlos con SPARQL)."""
        from rdflib import Graph

        g = Graph()
        for doc in self.listar(limite):
            g += a_grafo(doc)
        return g


# Consulta de ejemplo que cruza los informes (MongoDB) con la ontología (Fase 1):
# los informes solo guardan IRIs como mw:RecTextoAlternativo; el área y el texto
# de la recomendación salen de la ontología. Eso es posible porque son Linked Data.
Q_INFORMES_CON_ONTOLOGIA = """
PREFIX mw:     <http://www.semanticweb.org/sem-web-advisor/mantenimiento_web#>
PREFIX schema: <http://schema.org/>
PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?sitio ?estado ?recomendacion ?area
WHERE {
    ?informe a mw:InformeAuditoria ;
             mw:analizaSitio ?sitio ;
             mw:incluyeRecomendacion ?rec .
    ?sitio mw:tieneEstado ?e .
    ?e rdfs:label ?estado .
    ?rec rdfs:label ?recomendacion ;
         mw:aplicaPractica ?practica .
    ?practica a ?claseArea .
    ?claseArea rdfs:subClassOf mw:BuenasPracticas ; rdfs:label ?area .
    FILTER (?informe != mw:InformeEjemplo)   # excluir el ejemplo que trae la ontología
}
ORDER BY ?sitio ?area
"""


def grafo_con_ontologia(repo: "RepositorioInformes"):
    from ontologia.consultas import cargar_grafo

    g = repo.grafo()
    g += cargar_grafo()
    return g


def disponible(uri: str = URI_POR_DEFECTO) -> bool:
    try:
        RepositorioInformes(uri).verificar_conexion()
        return True
    except PyMongoError:
        return False


if __name__ == "__main__":
    repo = RepositorioInformes()
    print(f"MongoDB {repo.verificar_conexion()} - {repo.contar()} informes en {repo.col.full_name}\n")
    for doc in repo.listar(10):
        r = doc["result"]
        print(f"{doc['dateCreated']}  {doc['site']['@id']:<40} {doc['level']:<14} "
              f"{r['priority']:<5} {', '.join(r['tags'])}")

    g = grafo_con_ontologia(repo)
    print(f"\nGrafo RDF (informes + ontología): {len(g)} tripletas")
    print("SPARQL: recomendaciones de cada sitio y su área, según la ontología")
    for f in g.query(Q_INFORMES_CON_ONTOLOGIA):
        print(f"  {f.sitio}  [{f.estado}]  {f.area}: {f.recomendacion}")
