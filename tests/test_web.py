"""Pruebas de la Fase 5 (API Flask). Ejecutar desde la raíz:  python -m unittest discover tests -v

Los agentes se prueban de extremo a extremo en test_agentes.py; aquí se prueba la API
con un repositorio en memoria y sin arrancar SPADE.
"""
import unittest

from agentes.agente_experto import diagnosticar
from agentes.agente_notificador import estructurar_informe
from persistencia.repositorio import RepositorioMemoria
from web.app import crear_app


def informe(url, **cambios):
    m = {"url": url, "url_final": url + "/", "tiempo_carga": 0.5, "errores_sintaxis": 1, "imagenes_sin_alt": 0,
         "total_imagenes": 3, "enlaces_sin_texto": 0, "total_enlaces": 5, "sin_titulo": 0,
         "sin_meta_descripcion": 0, "sin_idioma": 0, "h1_incorrecto": 0, "total_h1": 1, "peso_html_kb": 30}
    m.update(cambios)
    return estructurar_informe(m, diagnosticar(m), "conv-prueba")


class TestApi(unittest.TestCase):

    def setUp(self):
        self.repo = RepositorioMemoria()
        self.id_ok = self.repo.guardar(informe("https://bien.ejemplo"))
        self.id_mal = self.repo.guardar(informe("https://mal.ejemplo", tiempo_carga=8, imagenes_sin_alt=5))
        self.repo.agregar_conversacion(self.id_mal, [{"de": "analista", "para": "experto", "performativa": "inform",
                                                      "resumen": "x", "hora": "10:00:00", "conversacion": "conv-prueba"}])
        self.cliente = crear_app(self.repo, iniciar_agentes=False).test_client()

    def test_salud(self):
        r = self.cliente.get("/api/salud").json
        self.assertEqual(r["informes"], 2)
        self.assertFalse(r["mongodb"])
        self.assertGreater(r["tripletas_ontologia"], 500)

    def test_listar_y_filtrar(self):
        todos = self.cliente.get("/api/informes").json
        self.assertEqual(len(todos), 2)
        filtrados = self.cliente.get("/api/informes?sitio=mal").json
        self.assertEqual([i["nivel"] for i in filtrados], ["Urgente"])

    def test_ver_informe_completo(self):
        v = self.cliente.get(f"/api/informes/{self.id_mal}").json
        self.assertEqual(v["estado"], "Crítico")
        self.assertTrue(v["diagnostico"]["recomendaciones"])
        self.assertEqual(len(v["mensajes"]), 1)
        self.assertIn("@context", v["jsonld"])
        self.assertNotIn("_id", v["jsonld"])
        self.assertGreater(v["tripletas"], 10)

    def test_descargar_jsonld(self):
        r = self.cliente.get(f"/api/informes/{self.id_ok}/jsonld")
        self.assertEqual(r.mimetype, "application/ld+json")
        self.assertIn("attachment", r.headers["Content-Disposition"])
        self.assertEqual(r.json["@type"], ["Report", "mw:InformeAuditoria"])

    def test_estadisticas(self):
        self.assertEqual(self.cliente.get("/api/estadisticas").json,
                         {"total": 2, "por_nivel": {"Urgente": 1, "Preventivo": 0, "Al día": 1}})

    def test_url_invalida_y_no_encontrados(self):
        r = self.cliente.post("/api/analisis", json={"url": "ftp://algo"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("dirección web válida", r.json["error"])
        self.assertEqual(self.cliente.get("/api/informes/no-existe").status_code, 404)
        self.assertEqual(self.cliente.get("/api/analisis/no-existe").status_code, 404)


if __name__ == "__main__":
    unittest.main()
