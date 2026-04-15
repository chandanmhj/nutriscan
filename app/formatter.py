NUTRIENT_DISPLAY = {
    "calories":        ("Calories",        ""),
    "total_fat_g":     ("Total fat",       "g"),
    "saturated_fat_g": ("  Saturated fat", "g"),
    "trans_fat_g":     ("  Trans fat",     "g"),
    "cholesterol_mg":  ("Cholesterol",     "mg"),
    "sodium_mg":       ("Sodium",          "mg"),
    "total_carbs_g":   ("Total carbs",     "g"),
    "dietary_fiber_g": ("  Dietary fiber", "g"),
    "sugar_g":         ("  Sugar",         "g"),
    "protein_g":       ("Protein",         "g"),
}

VERDICT_META = {
    "excellent": ("🟢", "Excellent"),
    "good":      ("🟢", "Good"),
    "moderate":  ("🟡", "Moderate"),
    "poor":      ("🔴", "Poor"),
    "avoid":     ("🔴", "Avoid"),
}


def build_message(nutrients: dict, flags: list) -> str:
    lines = []

    # ── Header ──────────────────────────────────────────
    product = nutrients.get("product_name", "This product")
    lines.append(f"*{product}*")
    lines.append("")

    # ── Overall verdict ─────────────────────────────────
    verdict = nutrients.get("overall_verdict", "moderate")
    icon, label = VERDICT_META.get(verdict, ("🟡", "Moderate"))
    lines.append(f"{icon} *Overall rating: {label}*")
    lines.append("")

    # ── Short summary ────────────────────────────────────
    summary = nutrients.get("short_summary")
    if summary:
        lines.append(f"📋 {summary}")
        lines.append("")

    # ── Nutrition table ──────────────────────────────────
    serving = nutrients.get("serving_size")
    if serving:
        lines.append(f"*Nutrition Facts* (per {serving})")
    else:
        lines.append("*Nutrition Facts* (per serving)")

    lines.append("──────────────────────")
    for key, (label, unit) in NUTRIENT_DISPLAY.items():
        val = nutrients.get(key)
        if val is None:
            continue
        lines.append(f"{label}: {val}{unit}")
    lines.append("──────────────────────")

    # ── Health flags ─────────────────────────────────────
    if flags:
        lines.append("")
        lines.append("*⚠️ Health Alerts*")
        for flag in flags:
            icon = "🔴" if flag.level == "danger" else "🟡"
            lines.append(f"{icon} {flag.message}")

    # ── Long term advice ─────────────────────────────────
    long_term = nutrients.get("long_term_advice")
    if long_term:
        lines.append("")
        lines.append(f"📅 *Long-term:* {long_term}")

    lines.append("")
    lines.append("_Values are per serving. Consult a doctor for personalised advice._")

    return "\n".join(lines)


def build_history_message(rows) -> str:
    if not rows:
        return "You have no scan history yet. Send a nutrition label photo to get started!"
    lines = ["*Your last scans*", ""]
    for i, row in enumerate(rows, 1):
        ts = row["query_time"][:16].replace("T", " ")
        flag = "🔴" if row["had_warnings"] else "✅"
        lines.append(f"{i}. {ts} UTC {flag}")
    return "\n".join(lines)