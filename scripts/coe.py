"""CoE prioritization: the only place where pipeline arithmetic happens.

Formula (official CoE guide):
    (Impacto*0.30)+(Eficiencia*0.20)+(Riesgo*0.15)+(Escalabilidad*0.10)+(Alineamiento*0.10)-(Complejidad*0.15)
"""

INSUFFICIENT = "No hay suficientes datos para establecer una calificación certera"
PENDING = "[PENDIENTE]"
GOVERNANCE_NOTICE = "Estos cambios deben ser validados antes de darse por finalizados."

# (key, display name, weight). Complexity subtracts, so its weight is negative.
DIMENSIONS = [
    ("impacto", "Impacto en Negocio", 0.30),
    ("eficiencia", "Eficiencia Operativa", 0.20),
    ("riesgo", "Riesgo Operativo", 0.15),
    ("escalabilidad", "Escalabilidad / Reutilización", 0.10),
    ("alineamiento", "Alineamiento Estratégico", 0.10),
    ("complejidad", "Complejidad Técnica (resta)", -0.15),
]


class CoeError(ValueError):
    pass


def _number(data, key, upper=None):
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or (upper is not None and value > upper):
        limit = f"entre 0 y {upper}" if upper is not None else "mayor o igual a 0"
        raise CoeError(f"evaluacion_coe.{key} debe ser un número {limit} o null (recibido: {value!r})")
    return value


def _score(data, key):
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
        raise CoeError(f"evaluacion_coe.{key} debe ser un entero entre 1 y 5 o null (recibido: {value!r})")
    return value


def monthly_hours(volume, minutes, pct):
    if volume is None or minutes is None or pct is None:
        return None
    return round(volume * minutes * (pct / 100) / 60, 1)


def efficiency_tier(hh):
    if hh is None:
        return None, INSUFFICIENT
    if hh > 100:
        return 5, ">100 hrs/mes"
    if hh >= 50:
        return 4, "50–100 hrs/mes"
    if hh >= 20:
        return 3, "20–50 hrs/mes"
    if hh >= 5:
        return 2, "5–20 hrs/mes"
    return 1, "<5 hrs/mes"


def evaluate(data):
    """Validate `evaluacion_coe` and return scores, points, final score and priority."""
    volume = _number(data, "volumen_mensual")
    minutes = _number(data, "tiempo_minutos_por_ejecucion")
    pct = _number(data, "pct_automatizacion", upper=100)
    hh = monthly_hours(volume, minutes, pct)
    eff_score, eff_label = efficiency_tier(hh)

    dimensions = []
    for key, name, weight in DIMENSIONS:
        if key == "eficiencia":
            score = eff_score
            detail = f"{eff_label} ({hh} HH/mes)" if hh is not None else eff_label
        else:
            score = _score(data, key)
            detail = data.get(f"{key}_justificacion") or "" if score is not None else INSUFFICIENT
        dimensions.append({
            "clave": key,
            "nombre": name,
            "score": score,
            "peso": f"{abs(weight):.0%}",
            "puntos": round(score * weight, 2) if score is not None else None,
            "detalle": detail,
        })

    if any(d["score"] is None for d in dimensions):
        final, priority = None, PENDING
    else:
        final = round(sum(d["score"] * w for d, (_, _, w) in zip(dimensions, DIMENSIONS)), 2)
        priority = "Alta" if final >= 3.5 else "Media" if final >= 2.5 else "Baja"

    return {
        "volumen_mensual": volume,
        "tiempo_minutos_por_ejecucion": minutes,
        "pct_automatizacion": pct,
        "hh_mensual": hh,
        "dimensiones": dimensions,
        "score": final,
        "prioridad": priority,
    }


def _show(value, suffix=""):
    return PENDING if value is None else f"{value}{suffix}"


def render_card(initiative, tower, systems, viable, discarded, result):
    """ASCII valuation card printed at the end of the pipeline."""
    rule, thin = "=" * 88, "-" * 88
    lines = [
        rule,
        "VALORIZACIÓN INICIAL CoE AUTOMATIZACIÓN TI".center(88),
        rule,
        f"Iniciativa: {initiative}",
        f"Torre: {tower or PENDING}    Sistemas: {systems or PENDING}",
        f"Casos Viables Asumidos: {', '.join(viable) or '-'}",
        f"Casos Descartados (Fuera de Alcance): {', '.join(discarded) or '-'}",
        thin,
        f"{'DIMENSIÓN':<30}{'SCORE':>6}{'PESO':>7}{'PUNTOS':>9}   JUSTIFICACIÓN PRELIMINAR",
        thin,
    ]
    for d in result["dimensiones"]:
        score = "-" if d["score"] is None else d["score"]
        points = "-" if d["puntos"] is None else d["puntos"]
        lines.append(f"{d['nombre']:<30}{score:>6}{d['peso']:>7}{points:>9}   {d['detalle']}")
    lines += [
        thin,
        f"SCORE FINAL CoE: {_show(result['score'])}  ==>  PRIORIDAD: {result['prioridad']}",
        rule,
        "MÉTRICAS ESTIMADAS:",
        f"- Volumen mensual: {_show(result['volumen_mensual'], ' eventos/mes')}",
        f"- Tiempo prom. ejecución: {_show(result['tiempo_minutos_por_ejecucion'], ' min/evento')}",
        f"- % Automatización: {_show(result['pct_automatizacion'], '%')}",
        f"- HH Mensuales Calculadas: {_show(result['hh_mensual'], ' HH/mes')}",
        thin,
        "AVISO DE GOBERNANZA:",
        GOVERNANCE_NOTICE,
        rule,
    ]
    return "\n".join(lines)
