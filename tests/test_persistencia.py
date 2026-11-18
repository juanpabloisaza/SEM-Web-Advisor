"""Pruebas de la Fase 4. Ejecutar desde la raíz:  python -m unittest discover tests -v"""
import unittest

from rdflib import RDF, Literal, Namespace, URIRef

from agentes.agente_experto import diagnosticar
from agentes.agente_notificador import estructurar_informe
from ontologia.consultas import MW
from persistencia.jsonld import a_grafo, construir_jsonld
from persistencia.repositorio import (Q_INFORMES_CON_ONTOLOGIA, RepositorioInformes, disponible,
                                      grafo_con_ontologia)

SCHEMA = Namespace("http://schema.org/")


def informe_de_prueba(**metricas):
    base = {"url": "https://tienda.ejemplo", "url_final": "https://tienda.ejemplo/", "tiempo_carga": 7.5,
            "errores_sintaxis": 3, "imagenes_sin_alt": 4, "enlaces_sin_texto": 0, "sin_titulo": 0,
            "sin_meta_descripcion": 1, "sin_idioma": 0, "h1_incorrecto": 0, "peso_html_kb": 40}
    base.update(metricas)
    return estructurar_informe(base, diagnosticar(base))


class TestJsonLd(unittest.TestCase):

    def setUp(self):
        self.informe = informe_de_prueba()
        self.doc = construir_jsonld(self.informe)

    def test_tiene_context_y_estructura_del_enunciado(self):
        self.assertIn("@context", self.doc)
        self.assertEqual(self.doc["@context"]["@vocab"], "http://schema.org/")
        self.assertIn("Report", self.doc["@type"])
        self.assertEqual(self.doc["site"]["@id"], "https://tienda.ejemplo/")
        self.assertEqual(set(self.doc["result"]), {"status", "priority", "tags"})
        self.assertEqual(self.doc["result"]["priority"], "Alta")  # 7.5 s -> Urgente
        self.assertIn("Accesibilidad", self.doc["result"]["tags"])

    def test_es_linked_data_valido(self):
        """Un procesador RDF lo entiende y enlaza con los individuos de la ontología."""
        g = a_grafo(self.doc)
        informe = URIRef(self.doc["@id"])
        sitio = URIRef("https://tienda.ejemplo/")
        self.assertIn((informe, RDF.type, SCHEMA.Report), g)
        self.assertIn((informe, RDF.type, MW.InformeAuditoria), g)
        self.assertIn((informe, MW.analizaSitio, sitio), g)
        self.assertIn((informe, MW.tieneNivel, MW.Urgente), g)
        self.assertIn((sitio, MW.tieneEstado, MW.Critico), g)
        self.assertIn((sitio, MW.presentaProblema, MW.ProblemaImagenesSinAlt), g)
        self.assertIn((informe, MW.incluyeRecomendacion, MW.RecCargaRapida), g)

    def test_todas_las_iris_mw_existen_en_la_ontologia(self):
        from ontologia.consultas import cargar_grafo

        onto = cargar_grafo()
        usados = {o for _, _, o in a_grafo(self.doc) if isinstance(o, URIRef) and str(o).startswith(str(MW))}
        usados |= {p for _, p, _ in a_grafo(self.doc) if str(p).startswith(str(MW))}
        faltantes = {u for u in usados if (u, None, None) not in onto}
        self.assertEqual(faltantes, set(), "IRIs usadas en el informe que la ontología no define")


@unittest.skipUnless(disponible(), "MongoDB no está corriendo en localhost:27017")
class TestRepositorioMongo(unittest.TestCase):

    def setUp(self):
        self.repo = RepositorioInformes(base_datos="sem_web_advisor_pruebas")
        self.repo.col.delete_many({})

    def tearDown(self):
        self.repo.cliente.drop_database("sem_web_advisor_pruebas")

    def test_guardar_y_leer(self):
        informe = informe_de_prueba()
        id_ = self.repo.guardar(informe)
        doc = self.repo.obtener(id_)
        self.assertEqual(doc["@context"]["mw"], str(MW))
        self.assertEqual(doc["level"], "mw:Urgente")
        self.assertEqual(self.repo.contar(), 1)

    def test_listar_y_estadisticas(self):
        self.repo.guardar(informe_de_prueba())
        self.repo.guardar(informe_de_prueba(tiempo_carga=0.5, imagenes_sin_alt=0, sin_meta_descripcion=0))
        self.assertEqual(len(self.repo.listar()), 2)
        self.assertEqual(self.repo.estadisticas(), {"mw:Urgente": 1, "mw:AlDia": 1})
        self.assertEqual(len(self.repo.listar(sitio="tienda")), 2)

    def test_lo_guardado_en_mongo_sigue_siendo_linked_data(self):
        """Lo que sale de MongoDB se puede cruzar con la ontología usando SPARQL."""
        self.repo.guardar(informe_de_prueba())
        g = grafo_con_ontologia(self.repo)
        areas = {str(f.area) for f in g.query(Q_INFORMES_CON_ONTOLOGIA)}
        self.assertEqual(areas, {"Accesibilidad", "Rendimiento", "SEO"})
        detalle = next(g.objects(None, MW.detalle))
        self.assertIsInstance(detalle, Literal)
        self.assertEqual(detalle.datatype, RDF.JSON)


if __name__ == "__main__":
    unittest.main()
