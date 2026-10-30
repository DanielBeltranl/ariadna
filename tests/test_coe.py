import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import coe  # noqa: E402

FULL = {
    "volumen_mensual": 600, "tiempo_minutos_por_ejecucion": 10, "pct_automatizacion": 100,
    "impacto": 4, "impacto_justificacion": "Incidentes prioritarios",
    "riesgo": 3, "riesgo_justificacion": "Tareas repetitivas",
    "escalabilidad": 3, "escalabilidad_justificacion": "Multi-equipo",
    "alineamiento": 4, "alineamiento_justificacion": "AIOps",
    "complejidad": 2, "complejidad_justificacion": "Automatización simple",
}


def dims(result):
    return {d["clave"]: d for d in result["dimensiones"]}


class EvaluateTest(unittest.TestCase):
    def test_full_data_computes_score_points_and_priority(self):
        r = coe.evaluate(FULL)
        # 600 * 10 min * 100% / 60 = 100 HH -> tier "50–100" = 4
        self.assertEqual(r["hh_mensual"], 100.0)
        d = dims(r)
        self.assertEqual(d["eficiencia"]["score"], 4)
        self.assertEqual(d["impacto"]["puntos"], 1.2)
        self.assertEqual(d["complejidad"]["puntos"], -0.3)
        # 1.2 + 0.8 + 0.45 + 0.3 + 0.4 - 0.3
        self.assertEqual(r["score"], 2.85)
        self.assertEqual(r["prioridad"], "Media")

    def test_priority_thresholds(self):
        high = dict(FULL, impacto=5, riesgo=5, escalabilidad=5, alineamiento=5, complejidad=1)
        self.assertEqual(coe.evaluate(high)["prioridad"], "Alta")
        low = dict(FULL, impacto=1, riesgo=1, escalabilidad=1, alineamiento=1, complejidad=5)
        self.assertEqual(coe.evaluate(low)["prioridad"], "Baja")

    def test_efficiency_tiers(self):
        cases = [(101, 5), (100, 4), (50, 4), (49.9, 3), (20, 3), (19.9, 2), (5, 2), (4.9, 1)]
        for hh, expected in cases:
            self.assertEqual(coe.efficiency_tier(hh)[0], expected, hh)

    def test_missing_qualitative_score_leaves_final_pending(self):
        r = coe.evaluate(dict(FULL, riesgo=None))
        d = dims(r)
        self.assertIsNone(d["riesgo"]["score"])
        self.assertIsNone(d["riesgo"]["puntos"])
        self.assertEqual(d["riesgo"]["detalle"], coe.INSUFFICIENT)
        self.assertIsNone(r["score"])
        self.assertEqual(r["prioridad"], coe.PENDING)

    def test_missing_volume_data_leaves_efficiency_pending(self):
        r = coe.evaluate(dict(FULL, pct_automatizacion=None))
        self.assertIsNone(r["hh_mensual"])
        self.assertIsNone(dims(r)["eficiencia"]["score"])
        self.assertEqual(dims(r)["eficiencia"]["detalle"], coe.INSUFFICIENT)
        self.assertEqual(r["prioridad"], coe.PENDING)

    def test_absent_keys_count_as_missing(self):
        r = coe.evaluate({})
        self.assertIsNone(r["score"])
        self.assertTrue(all(d["score"] is None for d in r["dimensiones"]))

    def test_invalid_scores_are_rejected(self):
        for bad in (0, 6, 3.5, "4", True):
            with self.assertRaises(coe.CoeError, msg=repr(bad)):
                coe.evaluate(dict(FULL, impacto=bad))

    def test_invalid_volume_data_is_rejected(self):
        for field, bad in (("volumen_mensual", "mucho"), ("volumen_mensual", -1), ("pct_automatizacion", 150)):
            with self.assertRaises(coe.CoeError, msg=f"{field}={bad!r}"):
                coe.evaluate(dict(FULL, **{field: bad}))


class CardTest(unittest.TestCase):
    def test_card_shows_values_and_governance_notice(self):
        card = coe.render_card("19-N1-COM-CL | Enlaces | MON", "N1", "Zabbix", ["UC-01"], ["UC-02"], coe.evaluate(FULL))
        self.assertIn("SCORE FINAL CoE: 2.85  ==>  PRIORIDAD: Media", card)
        self.assertIn("-0.3", card)
        self.assertIn("Estos cambios deben ser validados antes de darse por finalizados.", card)

    def test_card_marks_pending_values(self):
        card = coe.render_card("X", "", "", [], [], coe.evaluate({}))
        self.assertIn("SCORE FINAL CoE: [PENDIENTE]", card)
        self.assertIn(coe.INSUFFICIENT, card)


if __name__ == "__main__":
    unittest.main()
