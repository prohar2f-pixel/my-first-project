"""Search for market prices (Serper + LLM)."""

import logging
from decimal import Decimal

import httpx

from calculator import to_decimal
from config import SERPER_API_KEY, SERPER_API_URL, OPENROUTER_API_KEY, OPENROUTER_API_URL

logger = logging.getLogger(__name__)


async def search_price(name: str, unit: str | None, region: str) -> dict:
    """
    Search market price for material or work.
    Returns: {price_typical, price_min, price_max, confidence, source}
    """
    try:
        query = f"{name} {unit} цена {region}" if unit else f"{name} цена {region}"

        # Step 1: Search via Serper
        search_results = await _serper_search(query)

        # Step 2: Extract price from results via LLM
        price_data = await _llm_extract_price(name, unit, search_results)

        return price_data
    except Exception as e:
        logger.error(f"Price search failed for {name}: {e}")
        return {"price_typical": None, "price_min": None, "price_max": None, "confidence": "none", "source": None}


async def _serper_search(query: str) -> str:
    """Query Serper.dev for Russian market data."""
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "gl": "ru",
        "hl": "ru",
        "num": 10,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(SERPER_API_URL, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            # Combine organic results + snippets
            snippets = []
            for result in data.get("organic", [])[:5]:
                snippets.append(result.get("snippet", ""))

            return "\n".join(snippets)
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return ""


async def _llm_extract_price(name: str, unit: str | None, search_text: str) -> dict:
    """Extract price from Serper snippets using LLM."""
    prompt = f"""From the search results below, find the price for: {name}{' ' + unit if unit else ''}

Search results:
{search_text}

Return a JSON object:
{{
  "price_typical": <number or null>,
  "price_min": <number or null>,
  "price_max": <number or null>,
  "confidence": "high" or "medium" or "low" or "none",
  "source": "<url or brief source>"
}}

Only extract actual prices from search results. If no price found, return nulls with confidence="none".
Return ONLY JSON, no markdown."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-4-turbo",
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            import json
            price_data = json.loads(content)

            # Normalize prices to Decimal
            return {
                "price_typical": to_decimal(price_data.get("price_typical")),
                "price_min": to_decimal(price_data.get("price_min")),
                "price_max": to_decimal(price_data.get("price_max")),
                "confidence": price_data.get("confidence", "none"),
                "source": price_data.get("source"),
            }
        except Exception as e:
            logger.error(f"LLM price extraction failed: {e}")
            return {"price_typical": None, "price_min": None, "price_max": None, "confidence": "none", "source": None}
