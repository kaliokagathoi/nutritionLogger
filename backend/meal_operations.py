from csv_handler import CSVHandler
from ingredient_operations import IngredientOperations
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional


class MealOperations:
    def __init__(self, csv_handler: CSVHandler):
        self.csv_handler = csv_handler
        self.ingredient_ops = IngredientOperations(csv_handler)

    def create_meal(self, meal_name: str, ingredients: List[Dict]) -> Dict:
        """Create a new meal with list of ingredients and quantities"""
        meals_df = self.csv_handler.read_csv(self.csv_handler.meals_file)

        # Calculate total nutrition
        total_nutrition = self._calculate_total_nutrition(ingredients)

        # Prepare ingredient and quantity lists for storage
        ingredient_names = [ing['name'] for ing in ingredients]
        quantities = [ing['quantity'] for ing in ingredients]

        new_meal = {
            'meal_id': self.csv_handler.get_next_id(meals_df, 'meal_id'),
            'meal_name': meal_name,
            'ingredients_list': json.dumps(ingredient_names),
            'quantities_list': json.dumps(quantities),
            'total_calories': total_nutrition['calories'],
            'total_protein': total_nutrition['protein'],
            'total_fat_total': total_nutrition['fat_total'],
            'total_fat_saturated': total_nutrition['fat_saturated'],
            'total_carbohydrate': total_nutrition['carbohydrate'],
            'total_sugars': total_nutrition['sugars'],
            'total_dietary_fibre_g': total_nutrition['dietary_fibre_g'],
            'total_sodium_mg': total_nutrition['sodium_mg'],
            'total_calcium_mg': total_nutrition['calcium_mg'],
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        meals_df = pd.concat([meals_df, pd.DataFrame([new_meal])], ignore_index=True)
        self.csv_handler.write_csv(meals_df, self.csv_handler.meals_file)

        return new_meal

    def log_meal(self, meal_id: int, meal_time: str, date: str = None, notes: str = "") -> Dict:
        """Log a meal consumption"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # Get meal details
        meal = self.get_meal_by_id(meal_id)
        if not meal:
            raise ValueError(f"Meal with ID {meal_id} not found")

        meal_log_df = self.csv_handler.read_csv(self.csv_handler.meal_log_file)

        new_log = {
            'log_id': self.csv_handler.get_next_id(meal_log_df, 'log_id'),
            'date': date,
            'meal_time': meal_time,
            'meal_id': meal_id,
            'meal_name': meal['meal_name'],
            'ingredients_list': meal['ingredients_list'],
            'quantities_list': meal['quantities_list'],
            'total_calories': meal['total_calories'],
            'total_protein': meal['total_protein'],
            'total_fat_total': meal['total_fat_total'],
            'total_fat_saturated': meal['total_fat_saturated'],
            'total_carbohydrate': meal['total_carbohydrate'],
            'total_sugars': meal['total_sugars'],
            'total_dietary_fibre_g': meal['total_dietary_fibre_g'],
            'total_sodium_mg': meal['total_sodium_mg'],
            'total_calcium_mg': meal['total_calcium_mg'],
            'notes': notes
        }

        meal_log_df = pd.concat([meal_log_df, pd.DataFrame([new_log])], ignore_index=True)
        self.csv_handler.write_csv(meal_log_df, self.csv_handler.meal_log_file)

        return new_log

    def get_all_meals(self) -> List[Dict]:
        """Get all created meals"""
        meals_df = self.csv_handler.read_csv(self.csv_handler.meals_file)
        return meals_df.to_dict('records')

    def get_meal_by_id(self, meal_id: int) -> Optional[Dict]:
        """Get specific meal by ID"""
        meals_df = self.csv_handler.read_csv(self.csv_handler.meals_file)
        if meals_df.empty:
            return None

        meal = meals_df[meals_df['meal_id'] == meal_id]
        return meal.iloc[0].to_dict() if not meal.empty else None

    def _calculate_total_nutrition(self, ingredients: List[Dict]) -> Dict:
        """Calculate total nutrition for a list of ingredients with quantities"""
        totals = {
            'calories': 0, 'protein': 0, 'fat_total': 0, 'fat_saturated': 0,
            'carbohydrate': 0, 'sugars': 0, 'dietary_fibre_g': 0,
            'sodium_mg': 0, 'calcium_mg': 0
        }

        for ingredient in ingredients:
            nutrition = self.ingredient_ops.calculate_nutrition(
                ingredient['name'], ingredient['quantity']
            )
            for key in totals:
                totals[key] += nutrition.get(key, 0)

        # Round all values
        return {key: round(value, 2) for key, value in totals.items()}