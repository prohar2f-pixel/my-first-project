"""Extract works and materials from PDF using pdfplumber + LLM."""

import json
import logging
from decimal import Decimal
from typing import Optional

import pdfplumber
import httpx

from calculator import LineInput, to_decimal
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL
from openrouter_client import create_async_client

logger = logging.getLogger(__name__)

# System prompt for LLM: extract positions from PDF text
EXTRACT_SYSTEM_PROMPT = """You are a construction estimate parser.
Extract all line items from the text below.
Return a JSON array with each item:
{
  "type": "material" or "work",
  "name": "position name",
  "unit": "unit of measure (шт, м, м², л, кг, etc) or null",
  "qty": "quantity as string (e.g. '10', '0.5', '120 м²') or null",
  "raw": "original text line"
}

Guidelines:
- "материал", "краска", "кабель", "кирпич" → type: "material"
- "работа", "покраска", "прокладка", "монтаж" → type: "work"
- If type is unclear, guess from context (e.g. "краска" = material, "покраска" = work)
- Extract unit from qty if present (e.g. "120 м²" → qty="120", unit="м²")
- qty can be text; code will normalize it via to_decimal()
- Return ONLY valid JSON array, no markdown or extra text
"""


async def extract_positions_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from PDF and parse into positions (materials + works).
    Returns list of dicts: {type, name, unit, qty, raw}
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise

    if not text.strip():
        logger.warning("No text found in PDF")
        return []

    # Query LLM to extract positions
    positions = await _llm_extract_positions(text)
    return positions


async def _llm_extract_positions(text: str) -> list[dict]:
    """Query OpenRouter LLM to extract positions from text."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-4-turbo",
        "messages": [
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract positions:\n\n{text}"},
        ],
        "temperature": 0.3,
    }

    async with create_async_client() as client:
        try:
            response = await client.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Try to extract JSON from response
            try:
                positions = json.loads(content)
                if isinstance(positions, list):
                    return positions
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from LLM: {content[:100]}")
                return []

            return []
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []


def normalize_position(raw_pos: dict) -> Optional[LineInput]:
    """
    Convert LLM output dict → LineInput.
    Returns None if invalid/incomplete.
    """
    try:
        pos_type = raw_pos.get("type", "").lower()
        if pos_type not in ("material", "work"):
            return None

        name = raw_pos.get("name", "").strip()
        if not name:
            return None

        unit = raw_pos.get("unit", "").strip() or None
        qty_str = raw_pos.get("qty", "")
        qty = to_decimal(qty_str)

        return LineInput(
            type=pos_type,  # type: ignore
            name=name,
            unit=unit,
            qty=qty,
            unit_price=None,  # Will be filled by search.py
            confidence="none",  # Will be updated by search.py
            raw=raw_pos.get("raw"),
        )
    except Exception as e:
        logger.error(f"Failed to normalize position {raw_pos}: {e}")
        return None
