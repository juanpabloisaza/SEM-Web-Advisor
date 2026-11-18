"""Pruebas de la Fase 3. Ejecutar desde la raíz:  python -m unittest discover tests -v"""
import http.server
import threading
import unittest

import spade

from agentes.agente_experto import diagnosticar
from agentes.analizador import medir_html, normalizar_url
from agentes.mensajes import registro_acl
from agentes.sistema import ErrorAnalisis, SistemaMultiagente

PAGINA_CON_PROBLEMAS = """<!DOCTYPE html>
<html>
<head><title></title></head>
<body>
  <h1>Uno</h1><h1>Dos</h1>
  <img src="a.png"><img src="b.png" alt=""><img src="c.png" alt="Logo">
  <a href="/x"></a><a href="/y" aria-label="Inicio"></a><a href="/z">Contacto</a>
  <p><b>mal cerrado</p></i>
</body>
</html>"""

PAGINA_LIMPIA = """<!DOCTYPE html>
<html lang="es">
<head><title>Tienda de ejemplo</title><meta name="description" content="Una tienda de prueba"></head>
<body><h1>Bienvenidos</h1><img src="a.png" alt="Foto"><a href="/x">Productos</a></body>
</html>"""


class TestAnalizador(unittest.TestCase):

    def test_detecta_problemas_de_la_pagina(self):
        m = medir_html(PAGINA_CON_PROBLEMAS)
        self.assertEqual(m["imagenes_sin_alt"], 1)   # alt="" es válido (imagen decorativa)
        self.assertEqual(m["enlaces_sin_texto"], 1)  # el de aria-label sí está descrito
        self.assertEqual(m["sin_titulo"], 1)
        self.assertEqual(m["sin_meta_descripcion"], 1)
        self.assertEqual(m["sin_idioma"], 1)
        self.assertEqual(m["h1_incorrecto"], 1)
        self.assertGreater(m["errores_sintaxis"], 0)

    def test_pagina_limpia_no_tiene_problemas(self):
        m = medir_html(PAGINA_LIMPIA)
        for clave in ("imagenes_sin_alt", "enlaces_sin_texto", "sin_titulo", "sin_meta_descripcion",
                      "sin_idioma", "h1_incorrecto", "errores_sintaxis"):
            self.assertEqual(m[clave], 0, clave)

    def test_normalizar_url(self):
        self.assertEqual(normalizar_url(" ejemplo.com "), "https://ejemplo.com")
        with self.assertRaises(ValueError):
            normalizar_url("ftp://ejemplo.com")


class TestExperto(unittest.TestCase):

    def _metricas(self, **cambios):
        base = {"url": "http://x", "tiempo_carga": 0.5, "errores_sintaxis": 1, "imagenes_sin_alt": 0,
                "enlaces_sin_texto": 0, "sin_titulo": 0, "sin_meta_descripcion": 0, "sin_idioma": 0,
                "h1_incorrecto": 0, "peso_html_kb": 20}
        return {**base, **cambios}

    def test_sitio_perfecto(self):
        d = diagnosticar(self._metricas())
        self.assertEqual((d["nivel"], d["estado"], d["recomendaciones"]), ("Al día", "Excelente", []))
        self.assertIsNone(d["ajuste_semantico"])

    def test_problema_grave_sube_de_al_dia_a_preventivo(self):
        d = diagnosticar(self._metricas(imagenes_sin_alt=4))
        self.assertEqual(d["nivel_difuso"], "Al día")
        self.assertEqual(d["nivel"], "Preventivo")
        self.assertIn("prioridad Alta", d["ajuste_semantico"])
        self.assertEqual(d["areas_afectadas"], ["Accesibilidad"])

    def test_nunca_baja_un_veredicto_urgente(self):
        d = diagnosticar(self._metricas(tiempo_carga=8, errores_sintaxis=40))
        self.assertEqual((d["nivel"], d["estado"]), ("Urgente", "Crítico"))
        self.assertTrue(any(r["problema"] == "ProblemaCargaLenta" for r in d["recomendaciones"]))


class _Servidor(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/robots.txt":
            cuerpo, estado = b"User-agent: *\nDisallow: /privado\n", 200
        else:
            cuerpo, estado = PAGINA_CON_PROBLEMAS.encode(), 200
        self.send_response(estado)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass


class TestSistemaMultiagente(unittest.TestCase):
    """Prueba de extremo a extremo: 4 agentes reales intercambiando mensajes ACL."""

    @classmethod
    def setUpClass(cls):
        cls.http = http.server.HTTPServer(("127.0.0.1", 0), _Servidor)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()

    def test_flujo_completo_y_rechazo_por_robots(self):
        resultado = {}

        async def escenario():
            sistema = SistemaMultiagente()
            await sistema.iniciar()
            try:
                resultado["ok"] = await sistema.analizar(self.base + "/", timeout=30)
                try:
                    await sistema.analizar(self.base + "/privado", timeout=30)
                except ErrorAnalisis as e:
                    resultado["rechazo"] = str(e)
            finally:
                await sistema.detener()

        registro_acl.clear()
        spade.run(escenario(), embedded_xmpp_server=True)

        informe = resultado["ok"]["informe"]
        self.assertEqual(informe["sitio"], self.base + "/")
        self.assertTrue(informe["diagnostico"]["recomendaciones"])
        self.assertIn("robots.txt", resultado["rechazo"])

        # La conversación siguió el protocolo esperado
        pasos = [(m["de"], m["para"], m["performativa"]) for m in registro_acl]
        self.assertEqual(pasos[:5], [
            ("interfaz", "analista", "request"),
            ("analista", "interfaz", "agree"),
            ("analista", "experto", "inform"),
            ("experto", "notificador", "inform"),
            ("notificador", "interfaz", "inform"),
        ])
        self.assertIn(("analista", "interfaz", "refuse"), pasos)


if __name__ == "__main__":
    unittest.main()
