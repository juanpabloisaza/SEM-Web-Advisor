"""Pruebas de la Fase 2. Ejecutar desde la raíz:  python -m unittest discover tests -v"""
import unittest

from fuzzy.motor import REGLAS, describir, evaluar
from ontologia.consultas import interpretar_nivel


class TestMotorDifuso(unittest.TestCase):

    def test_sitio_rapido_y_limpio_esta_al_dia(self):
        self.assertEqual(evaluar(0.8, 2)["nivel"], "Al día")

    def test_regla_del_enunciado_lento_y_muchos_es_urgente(self):
        self.assertEqual(evaluar(9, 45)["nivel"], "Urgente")

    def test_lento_aunque_tenga_pocos_errores_es_urgente(self):
        self.assertEqual(evaluar(7.5, 3)["nivel"], "Urgente")

    def test_casos_intermedios_son_preventivos(self):
        self.assertEqual(evaluar(1.2, 35)["nivel"], "Preventivo")
        self.assertEqual(evaluar(3.5, 4)["nivel"], "Preventivo")

    def test_monotonia_mas_lento_nunca_mejora(self):
        """
        A igual cantidad de errores, más tiempo de carga nunca mejora el NIVEL.
        El puntaje puede oscilar unos pocos puntos (efecto conocido del centroide
        cuando dos reglas con la misma salida se activan a medias, p. ej. 5-6 s),
        pero nunca más de 5 puntos ni cambiando de nivel.
        """
        orden = {"Al día": 0, "Preventivo": 1, "Urgente": 2}
        for errores in (0, 15, 40):
            res = [evaluar(t / 2, errores) for t in range(0, 21)]
            for a, b in zip(res, res[1:]):
                self.assertLessEqual(orden[a["nivel"]], orden[b["nivel"]], f"errores={errores}")
                self.assertLess(a["puntaje"] - b["puntaje"], 5, f"errores={errores}")

    def test_transicion_gradual_sin_saltos(self):
        """2,9 s y 3,1 s deben dar puntajes cercanos (la razón de usar lógica difusa)."""
        self.assertLess(abs(evaluar(2.9, 8)["puntaje"] - evaluar(3.1, 8)["puntaje"]), 10)

    def test_valores_fuera_de_rango_se_recortan(self):
        r = evaluar(25, 300)
        self.assertEqual(r["entradas"], {"tiempo_carga": 10.0, "errores_sintaxis": 50.0})
        self.assertEqual(r["nivel"], "Urgente")
        self.assertEqual(evaluar(-1, -5)["nivel"], "Al día")

    def test_todas_las_combinaciones_tienen_regla(self):
        combinaciones = {(t, e) for t, e, _, _ in REGLAS}
        esperadas = {(t, e) for t in ("Rápido", "Moderado", "Lento") for e in ("Pocos", "Muchos")}
        self.assertEqual(combinaciones, esperadas)

    def test_siempre_hay_reglas_activadas_y_explicacion(self):
        for t in (0, 2.5, 5.5, 10):
            for e in (0, 15, 50):
                r = evaluar(t, e)
                self.assertTrue(r["reglas_activadas"], (t, e))
                self.assertIn(r["nivel"], describir(r))

    def test_niveles_existen_en_la_ontologia(self):
        """El veredicto difuso debe poder traducirse con la ontología (Fase 1)."""
        esperado = {"Al día": "Excelente", "Preventivo": "Aceptable", "Urgente": "Crítico"}
        for nivel, estado in esperado.items():
            self.assertEqual(interpretar_nivel(nivel)["estado"], estado)


if __name__ == "__main__":
    unittest.main()
