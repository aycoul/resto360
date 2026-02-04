"""OpenAI service for AI-powered menu features."""

import base64
import json
import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API interactions."""

    def __init__(self):
        self.api_key = getattr(settings, "OPENAI_API_KEY", None)
        self.model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        self.vision_model = getattr(settings, "OPENAI_VISION_MODEL", "gpt-4o")
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not configured in settings")
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client

    def generate_item_description(
        self,
        item_name: str,
        category: str,
        ingredients: Optional[str] = None,
        cuisine_type: str = "West African",
        language: str = "en",
    ) -> str:
        """
        Generate an appetizing description for a menu item.

        Args:
            item_name: Name of the menu item
            category: Category (e.g., "Main Dishes", "Desserts")
            ingredients: Optional comma-separated ingredients
            cuisine_type: Type of cuisine for context
            language: Output language code (en, fr)

        Returns:
            Generated description string
        """
        lang_instruction = (
            "Write in French." if language == "fr" else "Write in English."
        )

        ingredients_context = ""
        if ingredients:
            ingredients_context = f"\nKey ingredients: {ingredients}"

        prompt = f"""Generate a short, appetizing menu description for a restaurant dish.

Dish name: {item_name}
Category: {category}
Cuisine type: {cuisine_type}{ingredients_context}

{lang_instruction}

Requirements:
- 1-2 sentences maximum (under 150 characters ideal)
- Highlight flavors, textures, or cooking methods
- Make it sound appealing but not over-the-top
- Do not include the dish name in the description
- Do not use quotation marks

Example good descriptions:
- "Tender pieces marinated in aromatic spices, grilled to perfection"
- "A comforting blend of rich tomato sauce and slow-cooked vegetables"
- "Crispy on the outside, fluffy within, served with house-made sauce"

Generate only the description, nothing else:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional restaurant menu writer. Write concise, appetizing descriptions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip().strip('"')
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            raise

    def enhance_item_photo(self, image_data: bytes) -> dict:
        """
        Analyze a food photo and suggest improvements.

        Args:
            image_data: Raw image bytes

        Returns:
            Dict with analysis and suggestions
        """
        base64_image = base64.b64encode(image_data).decode("utf-8")

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert food photographer and stylist.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this food photo for a restaurant menu. Provide:
1. Quality score (1-10)
2. Brief description of what you see
3. 2-3 specific suggestions to improve the photo
4. Is this photo suitable for a professional menu? (yes/no/with-edits)

Respond in JSON format:
{
    "quality_score": 7,
    "description": "A plate of...",
    "suggestions": ["...", "..."],
    "menu_ready": "yes|no|with-edits"
}""",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low",
                                },
                            },
                        ],
                    },
                ],
                max_tokens=300,
            )
            content = response.choices[0].message.content
            # Parse JSON from response
            return json.loads(content)
        except json.JSONDecodeError:
            # Return raw text if not valid JSON
            return {
                "quality_score": 5,
                "description": "Unable to analyze",
                "suggestions": ["Try a different photo"],
                "menu_ready": "no",
            }
        except Exception as e:
            logger.error(f"Error analyzing photo: {e}")
            raise

    def extract_menu_from_image(self, image_data: bytes, language: str = "en") -> list:
        """
        Extract menu items from a photo of a physical menu (OCR).

        Args:
            image_data: Raw image bytes of menu
            language: Expected language of menu

        Returns:
            List of extracted menu items with name, description, price
        """
        base64_image = base64.b64encode(image_data).decode("utf-8")

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at reading and digitizing restaurant menus.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Extract all menu items from this menu image. The menu is in {language}.

For each item, extract:
- name: The dish name
- description: Any description (or null if none)
- price: The price as a number (no currency symbol)
- category: The section/category it belongs to

Return as a JSON array:
[
    {{"name": "...", "description": "...", "price": 3500, "category": "Main Dishes"}},
    ...
]

If you cannot read a price clearly, estimate based on similar items or use null.
If no items are visible, return an empty array [].""",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                max_tokens=2000,
            )
            content = response.choices[0].message.content

            # Try to extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse menu OCR response: {content}")
            return []
        except Exception as e:
            logger.error(f"Error extracting menu from image: {e}")
            raise

    def suggest_price(
        self,
        item_name: str,
        category: str,
        description: Optional[str] = None,
        location: str = "Dakar, Senegal",
        currency: str = "XOF",
    ) -> dict:
        """
        Suggest a price for a menu item based on market data.

        Args:
            item_name: Name of the item
            category: Category of the item
            description: Optional description
            location: Restaurant location for market context
            currency: Currency code

        Returns:
            Dict with suggested price range
        """
        prompt = f"""Suggest a price range for this restaurant menu item:

Item: {item_name}
Category: {category}
{f'Description: {description}' if description else ''}
Location: {location}
Currency: {currency}

Consider typical restaurant prices in {location} for this type of cuisine.

Respond in JSON format only:
{{
    "suggested_price": 3500,
    "price_range_low": 2500,
    "price_range_high": 4500,
    "reasoning": "Brief explanation"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a restaurant pricing consultant with expertise in West African markets.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"Error suggesting price: {e}")
            # Return default range
            return {
                "suggested_price": 3000,
                "price_range_low": 2000,
                "price_range_high": 5000,
                "reasoning": "Default pricing (AI unavailable)",
            }

    def translate_menu_item(
        self,
        name: str,
        description: Optional[str],
        source_lang: str,
        target_lang: str,
    ) -> dict:
        """
        Translate a menu item name and description.

        Args:
            name: Item name
            description: Item description
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Dict with translated name and description
        """
        lang_names = {"en": "English", "fr": "French", "wo": "Wolof", "ar": "Arabic"}
        source = lang_names.get(source_lang, source_lang)
        target = lang_names.get(target_lang, target_lang)

        prompt = f"""Translate this menu item from {source} to {target}:

Name: {name}
Description: {description or '(no description)'}

Keep translations natural and appetizing for a restaurant menu.
If the name is a traditional dish that shouldn't be translated, keep it and add a brief explanation.

Respond in JSON format only:
{{
    "name": "translated name",
    "description": "translated description or null if original was empty"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in restaurant menus and culinary terminology.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content.strip())
        except Exception as e:
            logger.error(f"Error translating: {e}")
            raise
