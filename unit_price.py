import json
import os
import re
from typing import Tuple, Dict, Any, List

class DataPreprocessor:
    """
    Reads the raw supermarkets.json and standardizes every item's package size
    into a mathematically comparable format (Natural Unit and True Unit Price).
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.raw_path = os.path.join(data_dir, "supermarkets.json")
        self.processed_path = os.path.join(data_dir, "supermarkets_processed.json")
        
    def needs_preprocessing(self) -> bool:
        if not os.path.exists(self.raw_path):
            return False
        if not os.path.exists(self.processed_path):
            return True
        # If raw is newer than processed, re-process
        return os.path.getmtime(self.raw_path) > os.path.getmtime(self.processed_path)

    def parse_natural_size(self, title: str, size_str: str) -> Tuple[float, str]:
        """
        Extracts the natural mathematical amount and unit from the product.
        Returns: (amount, unit_type) where unit_type is one of: 'L', 'KG', 'PIECE'
        """
        # Fallback to 1 piece if everything fails
        default = (1.0, 'PIECE')
        
        # 1. Check for pieces from title first (strongest indicator for eggs/toilet paper)
        piece_match = re.search(r'(\d+)\s*(?:stuks|st|pack|eieren)\b', title, re.IGNORECASE)
        if piece_match:
            return float(piece_match.group(1)), 'PIECE'
            
        if not size_str:
            return default
            
        ls = size_str.lower()
        
        # Extract the first valid number
        num_match = re.search(r'(\d+(?:[.,]\d+)?)', size_str)
        if not num_match:
            return default
            
        val = float(num_match.group(1).replace(',', '.'))
        
        # 2. Check for explicit piece strings in the size
        if re.search(r'\b(stuks|st|pack|eieren|stuk|x)\b', ls):
            return val, 'PIECE'
            
        # 3. Check for Liquids
        if re.search(r'\b(l|liter|liters)\b', ls):
            return val, 'L'
        if re.search(r'\b(ml|milliliter|milliliters)\b', ls):
            return val / 1000.0, 'L'
        if re.search(r'\b(cl|centiliter|centiliters)\b', ls):
            return val / 100.0, 'L'
        if re.search(r'\b(dl|deciliter|deciliters)\b', ls):
            return val / 10.0, 'L'
            
        # 4. Check for Weights
        if re.search(r'\b(kg|kilo|kilogram)\b', ls):
            return val, 'KG'
        if re.search(r'\b(g|gr|gram)\b', ls):
            return val / 1000.0, 'KG'
            
        # Default fallback
        return val, 'PIECE'

    def preprocess(self):
        print("Preprocessing dataset for unified unit pricing...")
        try:
            with open(self.raw_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for sm in data:
                for p in sm.get('d', []):
                    title = p.get('n', '')
                    size_str = p.get('s', '')
                    price = float(p.get('p', 0.0))
                    
                    amount, natural_unit = self.parse_natural_size(title, size_str)
                    p['parsed_amount'] = amount
                    p['natural_unit'] = natural_unit
                    
                    if amount > 0:
                        p['unit_price'] = round(price / amount, 4)
                    else:
                        p['unit_price'] = price
                        
            with open(self.processed_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
                
            print("Preprocessing complete.")
        except Exception as e:
            print(f"Failed to preprocess dataset: {e}")
