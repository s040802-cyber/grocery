import os
import json
from typing import List, Dict, Generator, Optional
from data_dictionary import DataManager

class AIService:
    """Base interface for AI interactions."""
    def parse_free_text_list(self, user_text: str, data_manager: DataManager) -> List[dict]:
        raise NotImplementedError

    def suggest_recipe_by_budget(self, budget: float, portions: int, partial_list: List[str], cuisine: str, bonus_items: List[str], model_name: Optional[str] = None) -> Generator[str, None, None]:
        raise NotImplementedError

    def generate_recipe(self, shopping_list: List[str], cuisine_type: str, model_name: Optional[str] = None) -> Generator[str, None, None]:
        raise NotImplementedError

    def modify_recipe(self, original_recipe: str, modification_prompt: str, shopping_list: List[str], model_name: Optional[str] = None) -> Generator[str, None, None]:
        raise NotImplementedError

class OpenAIService(AIService):
    def __init__(self, api_key: str):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("Please run 'pip install openai' to use OpenAIService")
        self.fast_model = "gpt-4o-mini" # Fast/cheap model for parsing

    def parse_free_text_list(self, user_text: str, data_manager: DataManager) -> List[dict]:
        valid_keys = list(data_manager.ingredients.keys())
        prompt = f"""
You are a smart shopping assistant. The user provided this messy shopping list: "{user_text}".
We have a dictionary of generic items (Valid keys: {valid_keys}).

Instructions:
1. If the user asks for a generic item (e.g., "milk", "apple"), map it to the closest exact key from our valid keys.
2. If the user explicitly asks for a SPECIFIC BRAND (e.g., "Campina milk", "Lipton ice tea") OR an item that does not exist in the valid keys, DO NOT map it to a generic key. 
3. Instead, translate the specific brand or unknown item into a Dutch supermarket search term and prefix it with 'DYNAMIC:'.
   - Example 1: "Campina milk" -> "DYNAMIC:campina melk"
   - Example 2: "Shimeji mushrooms" -> "DYNAMIC:beukenzwam"
4. Extract the requested quantity (amount) for each item. If not specified, default to 1.

Return ONLY a valid JSON object in this format: {{"items": [{{"id": "key1", "amount": 2}}, {{"id": "DYNAMIC:dutch_name", "amount": 1}}]}}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.fast_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("items", [])
        except Exception as e:
            print(f"OpenAI Parse Error: {e}")
            return []

    def suggest_recipe_by_budget(self, budget: float, portions: int, partial_list: List[str], cuisine: str, bonus_items: List[str], model_name: Optional[str] = None, max_supermarkets: int = 10) -> Generator[str, None, None]:
        model_to_use = model_name if model_name else self.fast_model
        prompt = f"""
You are a master chef. The user wants to cook a {cuisine} meal for {portions} people with a strict budget of €{budget}.
They already want to include these items: {partial_list}.
Here is a mix of Exciting Discounts and Budget Staples at their selected supermarkets: {bonus_items[:30]}.

CRITICAL RULE: You may select ingredients from AT MOST {max_supermarkets} distinct supermarkets. Count the unique supermarket tags like [AH] or [Jumbo] in your selection and ensure they do not exceed {max_supermarkets}.

PRICING & DISCOUNT RULES:
1. For any ingredient that you select from the provided "Exciting Discounts and Budget Staples" list, you MUST use the exact price and discount label (e.g. '(Discounted!)') as it is listed there.
2. For any other ingredient you add to complete the recipe that is NOT in the provided list, you MUST NOT invent or guess its price, and you MUST NOT label it as '(Discounted!)'. Simply list the ingredient and the supermarket name without a price (e.g., '- Garlic [AH]').
3. NEVER hallucinate or make up prices or discount tags for items that are not in the provided list of discounts/staples.
4. LINKING RULE: If an item in the provided list has a link (e.g., `(Link: https://...)`), you MUST copy that exact URL and include it next to the item in your final shopping list using markdown formatting: `[Item Name](https://...)`.

Invent a creative recipe prioritizing the Exciting Discounts and supplementing them with the Budget Staples to keep costs low. 
Provide a shopping list and step-by-step instructions. In your final shopping list, follow the PRICING & DISCOUNT RULES and the LINKING RULE above when writing the items and their prices/supermarkets.
"""
        try:
            stream = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.85,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n[AI Error: {str(e)}]"

    def generate_recipe(self, shopping_list: List[str], cuisine_type: str, model_name: Optional[str] = None) -> Generator[str, None, None]:
        model_to_use = model_name if model_name else self.fast_model
        prompt = f"""
You are a master chef. The user has this exact shopping list: {shopping_list}.
They want to cook a {cuisine_type} dish. Generate a step-by-step recipe using ONLY these ingredients (salt, pepper, oil assumed).
"""
        try:
            stream = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n[AI Error: {str(e)}]"

    def modify_recipe(self, original_recipe: str, modification_prompt: str, shopping_list: List[str], model_name: Optional[str] = None) -> Generator[str, None, None]:
        model_to_use = model_name if model_name else self.fast_model
        prompt = f"""
You are a master chef. The user has this exact shopping list: {shopping_list}.
CRITICAL RULE: This shopping list CANNOT be missed or completely replaced. You MUST heavily prioritize using these exact ingredients.

Here is the original recipe you generated:
{original_recipe}

The user wants to modify it with this request: "{modification_prompt}"

Rewrite the recipe to accommodate the request while strictly adhering to the critical rule above.
"""
        try:
            stream = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n[AI Error: {str(e)}]"

class GeminiService(AIService):
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
            self.fast_model = "gemini-3.5-flash" # Use fast model for parsing
        except ImportError:
            raise ImportError("Please run 'pip install google-generativeai' to use GeminiService")

    def parse_free_text_list(self, user_text: str, data_manager: DataManager) -> List[dict]:
        valid_keys = list(data_manager.ingredients.keys())
        prompt = f"""
You are a smart shopping assistant. The user provided this messy shopping list: "{user_text}".
We have a dictionary of generic items (Valid keys: {valid_keys}).

Instructions:
1. If the user asks for a generic item (e.g., "milk", "apple"), map it to the closest exact key from our valid keys.
2. If the user explicitly asks for a SPECIFIC BRAND (e.g., "Campina milk", "Lipton ice tea") OR an item that does not exist in the valid keys, DO NOT map it to a generic key. 
3. Instead, translate the specific brand or unknown item into a Dutch supermarket search term and prefix it with 'DYNAMIC:'.
   - Example 1: "Campina milk" -> "DYNAMIC:campina melk"
   - Example 2: "Shimeji mushrooms" -> "DYNAMIC:beukenzwam"
4. Extract the requested quantity (amount) for each item. If not specified, default to 1.

Return ONLY a valid JSON object in this format: {{"items": [{{"id": "key1", "amount": 2}}, {{"id": "DYNAMIC:dutch_name", "amount": 1}}]}}
"""
        try:
            model = self.genai.GenerativeModel(self.fast_model)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            return data.get("items", [])
        except Exception as e:
            print(f"Gemini Parse Error: {e}")
            return []

    def suggest_recipe_by_budget(self, budget: float, portions: int, partial_list: List[str], cuisine: str, bonus_items: List[str], model_name: Optional[str] = None, max_supermarkets: int = 10) -> Generator[str, None, None]:
        model_to_use = model_name if model_name else self.fast_model
        prompt = f"""
You are a master chef. The user wants to cook a {cuisine} meal for {portions} people with a strict budget of €{budget}.
They already want to include these items: {partial_list}.
Here is a mix of Exciting Discounts and Budget Staples at their selected supermarkets: {bonus_items[:30]}.

CRITICAL RULE: You may select ingredients from AT MOST {max_supermarkets} distinct supermarkets. Count the unique supermarket tags like [AH] or [Jumbo] in your selection and ensure they do not exceed {max_supermarkets}.

PRICING & DISCOUNT RULES:
1. For any ingredient that you select from the provided "Exciting Discounts and Budget Staples" list, you MUST use the exact price and discount label (e.g. '(Discounted!)') as it is listed there.
2. For any other ingredient you add to complete the recipe that is NOT in the provided list, you MUST NOT invent or guess its price, and you MUST NOT label it as '(Discounted!)'. Simply list the ingredient and the supermarket name without a price (e.g., '- Garlic [AH]').
3. NEVER hallucinate or make up prices or discount tags for items that are not in the provided list of discounts/staples.
4. LINKING RULE: If an item in the provided list has a link (e.g., `(Link: https://...)`), you MUST copy that exact URL and include it next to the item in your final shopping list using markdown formatting: `[Item Name](https://...)`.

Invent a creative recipe prioritizing the Exciting Discounts and supplementing them with the Budget Staples to keep costs low. 
Provide a shopping list and step-by-step instructions. In your final shopping list, follow the PRICING & DISCOUNT RULES and the LINKING RULE above when writing the items and their prices/supermarkets.
"""
        try:
            model = self.genai.GenerativeModel(model_to_use)
            response = model.generate_content(
                prompt, 
                stream=True,
                generation_config=self.genai.types.GenerationConfig(temperature=0.85)
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[AI Error: {str(e)}]"

    def generate_recipe(self, shopping_list: List[str], cuisine_type: str, model_name: Optional[str] = None) -> Generator[str, None, None]:
        model_to_use = model_name if model_name else self.fast_model
        prompt = f"""
You are a master chef. The user has this exact shopping list: {shopping_list}.
They want to cook a {cuisine_type} dish. Generate a step-by-step recipe using ONLY these ingredients (salt, pepper, oil assumed).
"""
        try:
            model = self.genai.GenerativeModel(model_to_use)
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[AI Error: {str(e)}]"

    def modify_recipe(self, original_recipe: str, modification_prompt: str, shopping_list: List[str], model_name: Optional[str] = None) -> Generator[str, None, None]:
        model_to_use = model_name if model_name else self.fast_model
        prompt = f"""
You are a master chef. The user has this exact shopping list: {shopping_list}.
CRITICAL RULE: This shopping list CANNOT be missed or completely replaced. You MUST heavily prioritize using these exact ingredients.

Here is the original recipe you generated:
{original_recipe}

The user wants to modify it with this request: "{modification_prompt}"

Rewrite the recipe to accommodate the request while strictly adhering to the critical rule above.
"""
        try:
            model = self.genai.GenerativeModel(model_to_use)
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[AI Error: {str(e)}]"

class AIFactory:
    @staticmethod
    def get_service() -> AIService:
        if "OPENAI_API_KEY" in os.environ:
            return OpenAIService(os.environ["OPENAI_API_KEY"])
        elif "GEMINI_API_KEY" in os.environ:
            return GeminiService(os.environ["GEMINI_API_KEY"])
        else:
            raise ValueError("No API key found in environment variables (OPENAI_API_KEY or GEMINI_API_KEY).")
