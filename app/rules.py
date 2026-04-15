from dataclasses import dataclass

THRESHOLDS = {
    "sugar_g":         {"danger": 12,  "warning": 6,   "label": "Sugar"},
    "sodium_mg":       {"danger": 600, "warning": 400,  "label": "Sodium"},
    "saturated_fat_g": {"danger": 5,   "warning": 3,    "label": "Saturated fat"},
    "trans_fat_g":     {"danger": 0.1, "warning": 0,    "label": "Trans fat"},
    "calories":        {"danger": 500, "warning": 300,  "label": "Calories"},
    "total_fat_g":     {"danger": 20,  "warning": 13,   "label": "Total fat"},
    "cholesterol_mg":  {"danger": 75,  "warning": 40,   "label": "Cholesterol"},
}


@dataclass
class NutrientFlag:
    nutrient: str
    value: float
    unit: str
    level: str
    message: str


def check(nutrients: dict) -> list:
    flags = []
    for key, limits in THRESHOLDS.items():
        raw = nutrients.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (ValueError, TypeError):
            continue

        label = limits["label"]
        unit = "mg" if "mg" in key else "g" if "_g" in key else ""

        if value >= limits["danger"]:
            flags.append(NutrientFlag(
                nutrient=label, value=value, unit=unit, level="danger",
                message=f"{label} is very high ({value}{unit}) — limit to avoid health risks.",
            ))
        elif value > limits["warning"]:
            flags.append(NutrientFlag(
                nutrient=label, value=value, unit=unit, level="warning",
                message=f"{label} is moderately high ({value}{unit}) — consume in moderation.",
            ))
    return flags