from csv_handler import CSVHandler
import pandas as pd
from typing import Dict, List, Optional


class IngredientOperations:
    def __init__(self, csv_handler: CSVHandler):
        self.csv_handler = csv_handler

    def get_all_ingredients(self) -> List[Dict]:
        """Get all ingredients from the CSV"""
        ingredients_df = self.csv_handler.read_csv(self.csv_handler.ingredients_file)
        return ingredients_df.to_dict('records')

    def get_ingredient_by_name(self, name: str) -> Optional[Dict]:
        """Get specific ingredient by name"""
        ingredients_df = self.csv_handler.read_csv(self.csv_handler.ingredients_file)
        if ingredients_df.empty:
            return None

        ingredient = ingredients_df[ingredients_df['name'] == name]
        return ingredient.iloc[0].to_dict() if not ingredient.empty else None

    def search_ingredients(self, query: str) -> List[Dict]:
        """Search ingredients by name"""
        ingredients_df = self.csv_handler.read_csv(self.csv_handler.ingredients_file)
        if ingredients_df.empty:
            return []

        mask = ingredients_df['name'].str.contains(query, case=False, na=False)
        return ingredients_df[mask].to_dict('records')

    def calculate_nutrition(self, ingredient_name: str, quantity: float) -> Dict:
        """Calculate nutrition for a given quantity of ingredient"""
        ingredient = self.get_ingredient_by_name(ingredient_name)
        if not ingredient:
            return {}

        unit_size = ingredient['unit_size']
        multiplier = quantity / unit_size

        return {
            'name': ingredient_name,
            'quantity': quantity,
            'unit_def': ingredient['unit_def'],
            'calories': round(ingredient['calories'] * multiplier, 2),
            'protein': round(ingredient['protein'] * multiplier, 2),
            'fat_total': round(ingredient['fat_total'] * multiplier, 2),
            'fat_saturated': round(ingredient['fat_saturated'] * multiplier, 2),
            'carbohydrate': round(ingredient['carbohydrate'] * multiplier, 2),
            'sugars': round(ingredient['sugars'] * multiplier, 2),
            'dietary_fibre_g': round(ingredient['dietary_fibre_g'] * multiplier, 2),
            'sodium_mg': round(ingredient['sodium_mg'] * multiplier, 2),
            'calcium_mg': round(ingredient['calcium_mg'] * multiplier, 2)
        }