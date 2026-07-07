import os
import json
import time
import datetime
import requests
import re
from typing import List, Dict, Optional, Set
import sys

# Monkey-patch requests to use a single global Session with Connection Pooling and a 30s timeout.
# Since SupermarktConnector uses `requests.get` (which opens/closes a new SSL connection every time),
# forcing it to use a Session will reuse TCP/TLS connections, making live API calls 5x-10x faster!
global_session = requests.Session()
class TimeoutAdapter(requests.adapters.HTTPAdapter):
    def send(self, request, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = 30.0
        return super().send(request, **kwargs)

global_session.mount('https://', TimeoutAdapter(pool_connections=20, pool_maxsize=20))
global_session.mount('http://', TimeoutAdapter(pool_connections=20, pool_maxsize=20))

requests.get = global_session.get
requests.post = global_session.post

# Ensure SupermarktConnector is in path
connector_path = os.path.join(os.path.dirname(__file__), 'scratch/SupermarktConnector')
if connector_path not in sys.path:
    sys.path.append(connector_path)

from data_dictionary import Ingredient, DataManager

class ProductResult:
    def __init__(self, name: str, brand: str, price: float, unit_size: str, unit_price: float, is_bonus: bool, url: str, parsed_amount: float = 1.0, natural_unit: str = "PIECE"):
        self.name = name
        self.brand = brand
        self.price = price
        self.unit_size = unit_size
        self.unit_price = unit_price
        self.is_bonus = is_bonus
        self.url = url
        self.parsed_amount = parsed_amount
        self.natural_unit = natural_unit

    def to_dict(self):
        return self.__dict__

class PriceEngine:
    """
    Hybrid Price Engine:
    - AH & Jumbo: Live API via SupermarktConnector
    - Lidl, Aldi, Vomar, Plus: Static checkjebon dataset with 7-day Bonus heuristic.
    """
    DATASET_URL = "https://raw.githubusercontent.com/supermarkt/checkjebon/main/data/supermarkets.json"
    REPO_API_URL = "https://api.github.com/repos/supermarkt/checkjebon/commits"
    DATA_PATH = "data/supermarkets.json"
    CACHE_DURATION_SECONDS = 24 * 60 * 60 # 24 hours
    BONUS_THRESHOLD = 0.25 # 25% drop

    def __init__(self, data_manager: DataManager, data_dir: str = "data"):
        self.data_manager = data_manager
        self.data_dir = os.path.join(os.path.dirname(__file__), data_dir)
        self.dataset_path = os.path.join(self.data_dir, "supermarkets.json")
        self.processed_path = os.path.join(self.data_dir, "supermarkets_processed.json")
        self.old_dataset_path = os.path.join(self.data_dir, "supermarkets_7days_ago.json")
        
        self.dataset = []
        self.old_dataset = []
        self.supermarket_data = {}
        self.bonus_items_keys: Set[str] = set()
        self.last_error = None
        
        self._initialize_dataset()
        
        # Initialize live connectors
        try:
            import sys
            connector_path = os.path.join(os.path.dirname(__file__), "scratch", "SupermarktConnector")
            if connector_path not in sys.path:
                sys.path.append(connector_path)
                
            from supermarktconnector.ah import AHConnector
            self.ah_connector = AHConnector()
            self.jumbo_connector = None # Jumbo live API is blocked by Cloudflare (403), using offline fallback
        except Exception as e:
            print(f"Warning: Failed to initialize AHConnector: {e}")
            self.ah_connector = None
            self.jumbo_connector = None

    def _initialize_dataset(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        download_needed = True
        if os.path.exists(self.dataset_path) and os.path.exists(self.old_dataset_path):
            file_age = time.time() - os.path.getmtime(self.dataset_path)
            if file_age < self.CACHE_DURATION_SECONDS:
                download_needed = False

        if download_needed:
            self._download_datasets()
            
        try:
            from unit_price import DataPreprocessor
            preprocessor = DataPreprocessor(self.data_dir)
            if preprocessor.needs_preprocessing():
                preprocessor.preprocess()
                
            with open(self.processed_path, "r", encoding="utf-8") as f:
                self.dataset = json.load(f)
            if os.path.exists(self.old_dataset_path):
                with open(self.old_dataset_path, "r", encoding="utf-8") as f:
                    self.old_dataset = json.load(f)
        except Exception as e:
            self.last_error = f"Failed to load dataset from disk: {e}"
            print(self.last_error)
            self.dataset = []
            self.old_dataset = []
            
        for sm in self.dataset:
            self.supermarket_data[sm.get("c")] = sm.get("d", [])
            
        self._compute_bonus_items()

    def _download_datasets(self):
        print("Downloading latest supermarket dataset...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            if "GITHUB_TOKEN" in os.environ:
                headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"
                
            response = requests.get(self.DATASET_URL, headers=headers, timeout=30)
            response.raise_for_status()
            with open(self.dataset_path, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            target_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
            commits_url = f"{self.REPO_API_URL}?path={self.DATA_PATH}&until={target_date}&per_page=1"
            c_resp = requests.get(commits_url, headers=headers, timeout=10)
            c_resp.raise_for_status()
            commits = c_resp.json()
            
            if commits:
                commit_sha = commits[0]["sha"]
                old_url = f"https://raw.githubusercontent.com/supermarkt/checkjebon/{commit_sha}/{self.DATA_PATH}"
                o_resp = requests.get(old_url, headers=headers, timeout=30)
                o_resp.raise_for_status()
                with open(self.old_dataset_path, "w", encoding="utf-8") as f:
                    f.write(o_resp.text)
            else:
                with open(self.old_dataset_path, "w", encoding="utf-8") as f:
                    f.write("[]")
        except Exception as e:
            self.last_error = f"Dataset download failed: {e}"
            print(self.last_error)

    def _compute_bonus_items(self):
        self.bonus_items_keys.clear()
        if not self.old_dataset or not self.dataset: return
            
        old_prices = {}
        for sm in self.old_dataset:
            c = sm.get("c")
            for p in sm.get("d", []):
                old_prices[f"{c}_{p.get('n')}"] = float(p.get("p", 0.0))
                
        for sm in self.dataset:
            c = sm.get("c")
            for p in sm.get("d", []):
                key = f"{c}_{p.get('n')}"
                new_price = float(p.get("p", 0.0))
                old_price = old_prices.get(key, 0.0)
                if old_price > 0 and new_price < old_price:
                    if (old_price - new_price) / old_price >= self.BONUS_THRESHOLD:
                        self.bonus_items_keys.add(key)

    def get_bonus_items(self, supermarket_id: str, limit: int = 50) -> List[ProductResult]:
        config = self.data_manager.get_supermarket(supermarket_id)
        if not config: return []
        
        sm_name = config.name
        results = []
        for sm in self.dataset:
            if sm.get("c") == sm_name:
                for p in sm.get("d", []):
                    p_name = p.get("n", "")
                    if f"{sm_name}_{p_name}" in self.bonus_items_keys:
                        price = float(p.get("p", 0.0))
                        results.append(ProductResult(
                            name=p_name, brand="", price=price, unit_size=p.get("s", ""),
                            unit_price=price, is_bonus=True, url=sm.get("u", "")
                        ))
                break
        return results[:limit]

    def get_hybrid_budget_items(self, supermarket_ids: List[str], limit: int = 20) -> List[str]:
        """Returns a mix of minor sudden price drops and randomized cheap staples,
        using Normalized Random Pooling to prevent supermarket size bias."""
        import random
        
        master_pool = []
        
        # 1. Map sm_ids to dataset names (sm.get("c"))
        sm_names = {}
        for sm_id in supermarket_ids:
            config = self.data_manager.get_supermarket(sm_id)
            if config:
                # The dataset uses exactly "AH", "Jumbo", "Lidl (via boodschaapje.nl)", etc.
                # Usually config.name matches, but for Lidl it might just be "Lidl" in our dictionary.
                # Let's map dynamically by checking what's in the dataset that contains the config name
                for dataset_sm_name in self.supermarket_data.keys():
                    if config.name.lower() in dataset_sm_name.lower():
                        sm_names[sm_id] = dataset_sm_name
                        break
                
        old_prices = {}
        for sm in self.old_dataset:
            dataset_name = sm.get("c")
            if dataset_name in sm_names.values():
                for p in sm.get("d", []):
                    old_prices[f"{dataset_name}_{p.get('n')}"] = float(p.get("p", 0.0))
                    
        for sm_id in supermarket_ids:
            if sm_id not in sm_names: continue
            dataset_name = sm_names[sm_id]
            config = self.data_manager.get_supermarket(sm_id)
            
            sm_drops = []
            sm_staples = []
            
            # Drops for this store
            for sm in self.dataset:
                if sm.get("c") == dataset_name:
                    for p in sm.get("d", []):
                        key = f"{dataset_name}_{p.get('n')}"
                        new_price = float(p.get("p", 0.0))
                        old_price = old_prices.get(key, 0.0)
                        if old_price > 0 and new_price < old_price * 0.95:
                            sm_drops.append(f"{p.get('n')} [{config.name}] (Discounted!)")
                    break
                    
            # Staples for this store
            products = self.supermarket_data.get(dataset_name, [])
            for p in products:
                price = float(p.get("p", 0.0))
                if price > 0.15:
                    sm_staples.append((f"{p.get('n')} [{config.name}]", price))
                    
            sm_staples.sort(key=lambda x: x[1])
            top_sm_staples = [item[0] for item in sm_staples[:100]]
            
            store_pool = sm_drops + top_sm_staples
            if len(store_pool) > 100:
                store_pool = random.sample(store_pool, 100)
                
            master_pool.extend(store_pool)
            
        if len(master_pool) <= limit:
            return master_pool
        return random.sample(master_pool, limit)

    def search(self, supermarket_id: str, ingredient: Ingredient) -> List[ProductResult]:
        config = self.data_manager.get_supermarket(supermarket_id)
        if not config: return []
        
        sm_name = config.name.lower()
        query = ingredient.translations.nl
        
        # Route to live scrapers if available
        if "ah" in sm_name or "albert" in sm_name:
            if self.ah_connector:
                live_res = self._search_ah_live(query, ingredient)
                if live_res: return live_res
        elif "jumbo" in sm_name:
            if self.jumbo_connector:
                live_res = self._search_jumbo_live(query, ingredient)
                if live_res: return live_res
                
        # Fallback to offline dataset
        return self._search_offline(config.name, query, ingredient)

    def _is_valid_product(self, p_name: str, ingredient: Ingredient) -> bool:
        for exclude in getattr(ingredient, "excluded_keywords", []):
            if re.compile(rf'\b{re.escape(exclude)}\b', re.IGNORECASE).search(p_name):
                return False
        return True

    def _matches_query(self, p_name: str, query: str) -> bool:
        """Ensures the product name actually contains the queried words."""
        query_words = query.lower().split()
        p_name_lower = p_name.lower()
        
        for word in query_words:
            if word == 'ei':
                if not re.search(r'\b(ei|eieren)\b', p_name_lower):
                    return False
            elif word == 'ui':
                if not re.search(r'\b(ui|uien)\b', p_name_lower):
                    return False
            elif word not in p_name_lower:
                return False
        return True

    def _search_ah_live(self, query: str, ingredient: Ingredient) -> List[ProductResult]:
        results = []
        try:
            res = self.ah_connector.search_products(query=query)
            products = res.get('products', [])
            
            for p in products:
                title = p.get('title', '')
                if not self._is_valid_product(title, ingredient): continue
                if not self._matches_query(title, query): continue
                
                is_bonus = p.get('isBonus', False)
                base_price = p.get('priceBeforeBonus', p.get('currentPrice', 0.0))
                if base_price is None:
                    base_price = p.get('currentPrice', 0.0)
                if not base_price: continue
                
                final_price = float(base_price)
                
                if is_bonus:
                    # Handle AH bonus logic
                    current_price = p.get('currentPrice')
                    labels = p.get('discountLabels', [])
                    
                    if current_price is not None:
                        final_price = float(current_price)
                    elif labels:
                        # Sometimes currentPrice is null but it's a 2 for 1.19 deal or 1+1 gratis
                        label = labels[0]
                        code = label.get('code', '')
                        count = label.get('count')
                        price = label.get('price')
                        free_count = label.get('freeCount')
                        percentage = label.get('percentage')
                        
                        if count and price is not None:
                            final_price = float(price) / float(count)
                        elif count and free_count:
                            # 1+1 gratis -> count=1, freeCount=1
                            total_items = float(count) + float(free_count)
                            final_price = float(base_price) * float(count) / total_items
                        elif code == 'DISCOUNT_ONE_HALF_PRICE':
                            # 2e halve prijs = buy 2, 2nd is 50% off -> average 25% discount per unit
                            final_price = float(base_price) * 0.75
                        elif percentage is not None:
                            final_price = float(base_price) * (1.0 - float(percentage) / 100.0)
                            
                unit_size = p.get('salesUnitSize', '')
                
                from unit_price import DataPreprocessor
                preprocessor = DataPreprocessor(self.data_dir)
                amount, natural_unit = preprocessor.parse_natural_size(title, unit_size)
                
                # AH Live fallback: calculate true unit price
                if amount > 0:
                    true_unit_price = round(final_price / amount, 4)
                else:
                    true_unit_price = final_price
                    
                # Standardize unit size string for display
                display_size = f"{amount} {natural_unit}" if natural_unit == "PIECE" else unit_size
                            
                results.append(ProductResult(
                    name=title,
                    brand=p.get('brand', ''),
                    price=final_price,
                    unit_size=display_size,
                    unit_price=true_unit_price,
                    is_bonus=is_bonus,
                    url=f"https://www.ah.nl/producten/product/{p.get('webshopId')}",
                    parsed_amount=amount,
                    natural_unit=natural_unit
                ))
        except Exception as e:
            print(f"AH Live Search Failed: {e}")
        return results

    def _search_jumbo_live(self, query: str, ingredient: Ingredient) -> List[ProductResult]:
        results = []
        try:
            res = self.jumbo_connector.search_products(query=query)
            products = res.get('products', {}).get('data', [])
            
            for p in products:
                title = p.get('title', '')
                if not self._is_valid_product(title, ingredient): continue
                
                prices = p.get('prices', {})
                price_info = prices.get('price', {})
                amount = price_info.get('amount', 0)
                
                if not amount: continue
                
                final_price = float(amount) / 100.0
                is_bonus = False
                
                # Jumbo bonus parsing
                promotions = p.get('promotions', [])
                if promotions:
                    is_bonus = True
                    # If there's a promo price, it's often in prices -> promoPrice
                    promo = prices.get('promoPrice')
                    if promo and promo.get('amount'):
                        final_price = float(promo.get('amount')) / 100.0
                
                results.append(ProductResult(
                    name=title,
                    brand='',
                    price=final_price,
                    unit_size=p.get('quantity', ''),
                    unit_price=final_price,
                    is_bonus=is_bonus,
                    url=f"https://www.jumbo.com/producten/{p.get('id')}"
                ))
        except Exception as e:
            print(f"Jumbo Live Search Failed: {e}")
        return results

    def _search_offline(self, sm_name: str, query: str, ingredient: Ingredient) -> List[ProductResult]:
        products = self.supermarket_data.get(sm_name, [])
        results = []
        
        for p in products:
            p_name = p.get("n", "")
            
            if self._matches_query(p_name, query):
                if not self._is_valid_product(p_name, ingredient): continue
                    
                key = f"{sm_name}_{p_name}"
                price = float(p.get("p", 0.0))
                if price <= 0.05: continue
                
                unit_size = p.get("s", "")
                parsed_amount = p.get("parsed_amount", 1.0)
                natural_unit = p.get("natural_unit", "PIECE")
                true_unit_price = p.get("unit_price", price)
                
                # Standardize for display
                display_size = f"{parsed_amount} {natural_unit}" if natural_unit == "PIECE" else unit_size
                
                results.append(ProductResult(
                    name=p_name, brand="", price=price, unit_size=display_size,
                    unit_price=true_unit_price, is_bonus=key in self.bonus_items_keys, url=p.get("u", ""),
                    parsed_amount=parsed_amount, natural_unit=natural_unit
                ))
        return results
