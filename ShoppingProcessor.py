from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Any
import math
import re
from data_dictionary import DataManager, Ingredient, Unit
from PriceEngine import PriceEngine, ProductResult

class ShoppingProcessor:
    """
    Orchestrates the shopping list pricing logic, concurrency, and routing.
    """
    def __init__(self, data_manager: DataManager, price_engine: PriceEngine):
        self.data_manager = data_manager
        self.price_engine = price_engine

    def process_shopping_list(self, items: List[str], amounts: Optional[Dict[str, int]] = None, selected_supermarkets: Optional[List[str]] = None, routing_strategy: str = "auto") -> Dict[str, Any]:
        """
        Main entry point.
        items: list of ingredient IDs (e.g. ["milk", "apple"])
        amounts: dict mapping ingredient IDs to quantities (e.g. {"milk": 2})
        selected_supermarkets: list of supermarket IDs (e.g. ["albert_heijn"]). If None, defaults to single best routing.
        routing_strategy: "auto", "single_best", or "mixed_basket"
        """
        self.amounts = amounts or {}
        ingredients = []
        for item_id in items:
            ing = self.data_manager.get_ingredient(item_id)
            if ing:
                ingredients.append(ing)

        available_supermarkets = selected_supermarkets or list(self.data_manager.supermarkets.keys())
        
        # Concurrent fetching
        raw_results = self._fetch_concurrently(ingredients, available_supermarkets)
        
        if routing_strategy == "single_best":
            return self._calculate_single_best(ingredients, raw_results, available_supermarkets)
        elif routing_strategy == "mixed_basket":
            return self._calculate_mixed_basket(ingredients, raw_results, available_supermarkets)
        else:
            if selected_supermarkets:
                return self._calculate_mixed_basket(ingredients, raw_results, available_supermarkets)
            else:
                return self._calculate_single_best(ingredients, raw_results, available_supermarkets)

    def _fetch_concurrently(self, ingredients: List[Ingredient], supermarkets: List[str]) -> Dict[str, Dict[str, List[ProductResult]]]:
        """
        Fetches all data sequentially (CPU-bound string matching avoids GIL overhead).
        Returns dict: { supermarket_id: { ingredient_id: [ProductResult...] } }
        """
        results = {sm: {ing.id: [] for ing in ingredients} for sm in supermarkets}
        
        for sm in supermarkets:
            for ing in ingredients:
                try:
                    products = self.price_engine.search(sm, ing)
                    qty = getattr(self, "amounts", {}).get(ing.id, 1)
                    results[sm][ing.id] = self._filter_and_sort(products, ing, qty)[:20] # CAP AT 20 TO PREVENT GUI FREEZE
                except Exception as e:
                    print(f"Error in fetch task: {e}")
                    
        return results

    @staticmethod
    def _is_compatible_unit(natural_unit: str, expected_unit: Unit) -> bool:
        """
        Checks if the product's natural unit is mathematically compatible with the recipe's expected unit.
        Returns False if trying to fulfill a LITER requirement with PIECES (e.g. toilet paper).
        """
        if natural_unit == "PIECE" and expected_unit != Unit.PIECE:
            return False
        if natural_unit != "PIECE" and expected_unit == Unit.PIECE:
            return False
        # KG and LITER are loosely interchangeable for things like yogurt, so allow them.
        return True

    def _filter_and_sort(self, products: List[ProductResult], ing: Ingredient, requested_qty: float) -> List[ProductResult]:
        """
        Filters products to avoid false matches and sorts by actual fulfillment cost
        for the requested quantity.
        """
        valid_products = []
        for p in products:
            if p.price <= 0: continue
            
            # Apply negative keyword filtering (left-boundary only)
            is_excluded = False
            for exclude in getattr(ing, "excluded_keywords", []):
                if re.compile(rf'\b{re.escape(exclude)}', re.IGNORECASE).search(p.name):
                    is_excluded = True
                    break
            if is_excluded: continue
            
            if not self._is_compatible_unit(p.natural_unit, ing.expected_unit):
                continue
            
            valid_products.append(p)
            
        # Already pre-calculated true unit price in DataPreprocessor!
        # Sort strictly by the true unit price (price per piece, per liter, etc.)
        return sorted(valid_products, key=lambda p: p.unit_price)

    def _calculate_mixed_basket(self, ingredients: List[Ingredient], raw_results: Dict[str, Dict[str, List[ProductResult]]], supermarkets: List[str]) -> Dict[str, Any]:
        """
        Optimizes for the absolute cheapest item across the selected supermarkets.
        """
        basket_items = []
        total_cost = 0.0
        missing_items = []

        for ing in ingredients:
            best_product = None
            best_sm = None
            
            for sm in supermarkets:
                products = raw_results[sm][ing.id]
                if products:
                    top_product = products[0]
                    if not best_product or top_product.unit_price < best_product.unit_price:
                        best_product = top_product
                        best_sm = sm
                        
            if best_product:
                qty = self.amounts.get(ing.id, 1)
                
                # Conversion to GRAM/ML if needed (natural unit is KG/L but recipe wants GRAM/ML)
                package_size = best_product.parsed_amount
                if ing.expected_unit in [Unit.GRAM, Unit.ML] and best_product.natural_unit in ["KG", "L"]:
                    package_size = package_size * 1000.0
                elif ing.expected_unit in [Unit.KG, Unit.LITER] and best_product.natural_unit in ["KG", "L"]:
                    pass # Keep natural size
                    
                packages_needed = math.ceil(qty / package_size) if package_size > 0 else 1
                total_cost += best_product.price * packages_needed
                raw_alts = [
                    {"name": p.name, "price": p.price, "is_bonus": p.is_bonus, "supermarket": sm_iter, "unit_size": p.unit_size, "unit_price": p.unit_price, "parsed_amount": p.parsed_amount, "natural_unit": p.natural_unit} 
                    for sm_iter in supermarkets 
                    for p in raw_results[sm_iter][ing.id]
                ]
                raw_alts.sort(key=lambda x: x["unit_price"])
                
                basket_items.append({
                    "ingredient_id": ing.id,
                    "name": best_product.name,
                    "price": best_product.price,
                    "total_price": best_product.price * packages_needed,
                    "amount": qty,
                    "packages_needed": packages_needed,
                    "expected_unit": ing.expected_unit.value,
                    "supermarket": best_sm,
                    "is_bonus": best_product.is_bonus,
                    "alternatives": raw_alts[:25]
                })
            else:
                missing_items.append(ing.id)

        return {
            "routing_strategy": "mixed_basket",
            "total_cost": round(total_cost, 2),
            "items": basket_items,
            "missing_items": missing_items
        }

    def _calculate_single_best(self, ingredients: List[Ingredient], raw_results: Dict[str, Dict[str, List[ProductResult]]], supermarkets: List[str]) -> Dict[str, Any]:
        """
        Evaluates the single cheapest destination for the entire list.
        Applies Strict Fulfillment Check.
        """
        sm_evaluations = {}
        
        for sm in supermarkets:
            total = 0.0
            found_count = 0
            items = []
            
            for ing in ingredients:
                qty = self.amounts.get(ing.id, 1)
                products = raw_results[sm][ing.id]
                if products:
                    top_product = products[0]
                    
                    package_size = top_product.parsed_amount
                    if ing.expected_unit in [Unit.GRAM, Unit.ML] and top_product.natural_unit in ["KG", "L"]:
                        package_size = package_size * 1000.0
                        
                    packages_needed = math.ceil(qty / package_size) if package_size > 0 else 1
                    total += top_product.price * packages_needed
                    found_count += 1
                    raw_alts = [
                        {"name": p.name, "price": p.price, "is_bonus": p.is_bonus, "supermarket": alt_sm, "unit_size": p.unit_size, "unit_price": p.unit_price, "parsed_amount": p.parsed_amount, "natural_unit": p.natural_unit} 
                        for alt_sm in supermarkets 
                        for p in raw_results[alt_sm][ing.id]
                    ]
                    raw_alts.sort(key=lambda x: x["unit_price"])
                    
                    items.append({
                        "ingredient_id": ing.id,
                        "name": top_product.name,
                        "price": top_product.price,
                        "total_price": top_product.price * packages_needed,
                        "amount": qty,
                        "packages_needed": packages_needed,
                        "expected_unit": ing.expected_unit.value,
                        "supermarket": sm,
                        "is_bonus": top_product.is_bonus,
                        "alternatives": raw_alts[:25]
                    })
            
            sm_evaluations[sm] = {
                "total": total,
                "found_count": found_count,
                "items": items
            }

        # Strict Fulfillment Check
        total_ingredients = len(ingredients)
        strict_candidates = {sm: data for sm, data in sm_evaluations.items() if data["found_count"] == total_ingredients}
        
        if strict_candidates:
            # Pick cheapest from strict candidates
            best_sm = min(strict_candidates.keys(), key=lambda k: strict_candidates[k]["total"])
            best_data = strict_candidates[best_sm]
            return {
                "routing_strategy": "single_best_strict",
                "destination": best_sm,
                "total_cost": round(best_data["total"], 2),
                "items": best_data["items"],
                "missing_items": [],
                "all_candidates": strict_candidates
            }
        else:
            # Fallback: Highest fulfillment rate
            best_sm = max(sm_evaluations.keys(), key=lambda k: sm_evaluations[k]["found_count"])
            best_data = sm_evaluations[best_sm]
            
            found_ids = [item["ingredient_id"] for item in best_data["items"]]
            missing_items = [ing.id for ing in ingredients if ing.id not in found_ids]
            
            fallback_candidates = {sm: data for sm, data in sm_evaluations.items() if data["found_count"] == best_data["found_count"]}
            
            return {
                "routing_strategy": "single_best_fallback",
                "destination": best_sm,
                "total_cost": round(best_data["total"], 2),
                "items": best_data["items"],
                "missing_items": missing_items,
                "all_candidates": fallback_candidates
            }
