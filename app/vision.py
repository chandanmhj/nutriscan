import base64
import json
import os
import re
import asyncio
import httpx

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=" + GEMINI_API_KEY

PROMPT = """You are a nutrition label reader and diet advisor. Extract all nutrients from this image and return ONLY a valid JSON object with no extra text.

Use these exact keys where available (all values as numbers, not strings):
  calories, total_fat_g, saturated_fat_g, trans_fat_g, cholesterol_mg,
  sodium_mg, total_carbs_g, dietary_fiber_g, sugar_g, protein_g,
  vitamin_d_mcg, calcium_mg, iron_mg, potassium_mg

Also include:
  serving_size (string, e.g. "1 cup (240ml)")
  servings_per_container (number or null)
  product_name (string, guess from context if visible, else "This product")
  overall_verdict (string, one of: "excellent" | "good" | "moderate" | "poor" | "avoid")
  short_summary (string, 1-2 sentences of plain English diet advice — e.g. how often this can be consumed, who it suits, what makes it good or bad. Be specific and conversational.)
  long_term_advice (string, 1 sentence about long-term daily consumption impact)

Verdict guide:
- excellent: very balanced, low sugar/sodium/fat, good protein/fiber — can be eaten daily
- good: mostly healthy with minor concerns — fine for regular consumption
- moderate: some concerning values — okay occasionally, not daily
- poor: multiple high values — limit consumption
- avoid: very high sugar/sodium/trans fat — not recommended

If a value is not visible, omit that key.
Return ONLY the JSON object — no markdown, no explanation."""


async def _call_model(client: httpx.AsyncClient, model: str, b64: str, mime_type: str) -> dict:
    url = BASE_URL.format(model=model)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {"mime_type": mime_type, "data": b64}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0},
    }
    response = await client.post(url, json=payload)
    response.raise_for_status()
    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


async def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    async with httpx.AsyncClient(timeout=60) as client:
        for attempt in range(3):  # 3 retries total
            for model in MODELS:
                try:
                    return await _call_model(client, model, b64, mime_type)
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status in (503, 429, 500):
                        # Server-side issue — wait and retry
                        wait = 5 * (attempt + 1)
                        print(f"[{model}] {status} — retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    elif status == 404:
                        # Model not available — try next model
                        print(f"[{model}] 404 — trying next model...")
                        break
                    else:
                        raise
                except json.JSONDecodeError as e:
                    raise ValueError(f"Could not parse response: {e}")

    raise ValueError("All Gemini models failed after retries. Please try again in a moment.")