"""Menu translation service."""

import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class MenuTranslator:
    """Service for translating menu content."""

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "fr": "French",
        "wo": "Wolof",
        "ar": "Arabic",
        "pt": "Portuguese",
        "es": "Spanish",
    }

    def __init__(self):
        self.openai_api_key = getattr(settings, "OPENAI_API_KEY", None)
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.openai_api_key)
            except ImportError:
                raise ImportError("openai package not installed")
        return self._client

    def translate_menu(
        self,
        items: list[dict],
        source_lang: str,
        target_lang: str,
    ) -> list[dict]:
        """
        Translate a list of menu items.

        Args:
            items: List of menu items with name and description
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of items with translated fields
        """
        if source_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported source language: {source_lang}")
        if target_lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported target language: {target_lang}")

        if source_lang == target_lang:
            return items

        source_name = self.SUPPORTED_LANGUAGES[source_lang]
        target_name = self.SUPPORTED_LANGUAGES[target_lang]

        # Build batch for translation
        items_text = []
        for i, item in enumerate(items):
            items_text.append(f"{i}. {item.get('name', '')} | {item.get('description', '')}")

        prompt = f"""Translate the following menu items from {source_name} to {target_name}.

Format: Each line is "index. name | description"
Keep traditional dish names and add explanations if needed.
If a description is empty, leave it empty.

Items to translate:
{chr(10).join(items_text)}

Respond with translations in the same format (index. name | description):"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator for restaurant menus. Preserve culinary terms appropriately.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.3,
            )

            content = response.choices[0].message.content
            translated_items = []

            # Parse response
            for line in content.strip().split("\n"):
                if ". " not in line:
                    continue

                try:
                    idx_str, rest = line.split(". ", 1)
                    idx = int(idx_str.strip())

                    if " | " in rest:
                        name, description = rest.split(" | ", 1)
                    else:
                        name = rest
                        description = ""

                    if idx < len(items):
                        translated = items[idx].copy()
                        translated["name"] = name.strip()
                        if description.strip():
                            translated["description"] = description.strip()
                        translated_items.append(translated)
                except (ValueError, IndexError):
                    continue

            # Fill in any missing items with originals
            result = []
            for i, item in enumerate(items):
                matching = next(
                    (t for t in translated_items if items.index(item) == i),
                    item,
                )
                result.append(matching)

            return result

        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise

    def translate_single(
        self,
        name: str,
        description: Optional[str],
        source_lang: str,
        target_lang: str,
    ) -> dict:
        """
        Translate a single menu item.

        Args:
            name: Item name
            description: Item description
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Dict with translated name and description
        """
        items = [{"name": name, "description": description or ""}]
        translated = self.translate_menu(items, source_lang, target_lang)
        if translated:
            return {
                "name": translated[0].get("name", name),
                "description": translated[0].get("description") or None,
            }
        return {"name": name, "description": description}

    def detect_language(self, text: str) -> str:
        """
        Detect the language of text.

        Args:
            text: Text to analyze

        Returns:
            Language code
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"What language is this text? Reply with only the ISO 639-1 code (en, fr, wo, ar, etc.): {text[:500]}",
                    },
                ],
                max_tokens=10,
                temperature=0,
            )
            code = response.choices[0].message.content.strip().lower()
            return code if code in self.SUPPORTED_LANGUAGES else "en"
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "en"
