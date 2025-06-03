from csv_handler import CSVHandler
from ingredient_operations import IngredientOperations
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class MealOperations:
    def __init__(self, csv_handler: CSVHandler):
        self.csv_handler = csv_handler
        self.ingredient_ops = IngredientOperations(csv_handler)

        # Daily nutrition file path
        self.daily_nutrition_file = os.path.join(csv_handler.data_dir, "daily_nutrition.csv")
        self._initialize_daily_nutrition_file()

        # Ensure servings_remaining column exists in meals.csv
        self.csv_handler.ensure_servings_remaining_column()

    def _initialize_daily_nutrition_file(self):
        """Create daily nutrition CSV file if it doesn't exist"""
        import os
        if not os.path.exists(self.daily_nutrition_file):
            daily_nutrition_df = pd.DataFrame(columns=[
                'entry_id', 'date', 'meal_id', 'meal_name', 'servings_consumed',
                'calories_consumed', 'protein_consumed', 'fat_total_consumed',
                'fat_saturated_consumed', 'carbohydrate_consumed', 'sugars_consumed',
                'dietary_fibre_consumed', 'sodium_consumed', 'calcium_consumed',
                'added_timestamp'
            ])
            daily_nutrition_df.to_csv(self.daily_nutrition_file, index=False)

    def create_meal(self, meal_name: str, servings: int, ingredients: List[Dict]) -> Dict:
        """Create a new meal with list of ingredients, quantities, and servings"""
        meals_df = self.csv_handler.read_csv(self.csv_handler.meals_file)

        # Calculate total nutrition
        total_nutrition = self._calculate_total_nutrition(ingredients)

        # Calculate per-serving nutrition
        per_serving_nutrition = self._calculate_per_serving_nutrition(total_nutrition, servings)

        # Prepare ingredient and quantity lists for storage
        ingredient_names = [ing['name'] for ing in ingredients]
        quantities = [ing['quantity'] for ing in ingredients]

        new_meal = {
            'meal_id': self.csv_handler.get_next_id(meals_df, 'meal_id'),
            'meal_name': meal_name,
            'servings': servings,
            'servings_remaining': servings,  # NEW: Initialize servings_remaining to servings
            'ingredients_list': json.dumps(ingredient_names),
            'quantities_list': json.dumps(quantities),
            # Total nutrition
            'total_calories': total_nutrition['calories'],
            'total_protein': total_nutrition['protein'],
            'total_fat_total': total_nutrition['fat_total'],
            'total_fat_saturated': total_nutrition['fat_saturated'],
            'total_carbohydrate': total_nutrition['carbohydrate'],
            'total_sugars': total_nutrition['sugars'],
            'total_dietary_fibre_g': total_nutrition['dietary_fibre_g'],
            'total_sodium_mg': total_nutrition['sodium_mg'],
            'total_calcium_mg': total_nutrition['calcium_mg'],
            # Per serving nutrition
            'calories_per_serving': per_serving_nutrition['calories'],
            'protein_per_serving': per_serving_nutrition['protein'],
            'fat_total_per_serving': per_serving_nutrition['fat_total'],
            'fat_saturated_per_serving': per_serving_nutrition['fat_saturated'],
            'carbohydrate_per_serving': per_serving_nutrition['carbohydrate'],
            'sugars_per_serving': per_serving_nutrition['sugars'],
            'dietary_fibre_per_serving': per_serving_nutrition['dietary_fibre_g'],
            'sodium_per_serving': per_serving_nutrition['sodium_mg'],
            'calcium_per_serving': per_serving_nutrition['calcium_mg'],
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        meals_df = pd.concat([meals_df, pd.DataFrame([new_meal])], ignore_index=True)
        self.csv_handler.write_csv(meals_df, self.csv_handler.meals_file)

        return new_meal

    def add_meal_to_daily_nutrition(self, date: str, meal_id: int, servings_consumed: float) -> Dict:
        """Add a meal to daily nutrition tracking"""
        # Get meal details
        meal = self.get_meal_by_id(meal_id)
        if not meal:
            raise ValueError(f"Meal with ID {meal_id} not found")

        # Check if enough servings are available (only for new meals with servings_remaining data)
        servings_remaining = meal.get('servings_remaining')
        if servings_remaining is not None and not pd.isna(servings_remaining):
            if float(servings_remaining) < servings_consumed:
                available = float(servings_remaining)
                raise ValueError(
                    f"Not enough servings available. Requested: {servings_consumed}, Available: {available}")

        daily_nutrition_df = self.csv_handler.read_csv(self.daily_nutrition_file)

        # Calculate nutrition for consumed servings
        consumed_nutrition = self._calculate_consumed_nutrition(meal, servings_consumed)

        new_entry = {
            'entry_id': self.csv_handler.get_next_id(daily_nutrition_df, 'entry_id'),
            'date': date,
            'meal_id': meal_id,
            'meal_name': meal['meal_name'],
            'servings_consumed': servings_consumed,
            'calories_consumed': consumed_nutrition['calories'],
            'protein_consumed': consumed_nutrition['protein'],
            'fat_total_consumed': consumed_nutrition['fat_total'],
            'fat_saturated_consumed': consumed_nutrition['fat_saturated'],
            'carbohydrate_consumed': consumed_nutrition['carbohydrate'],
            'sugars_consumed': consumed_nutrition['sugars'],
            'dietary_fibre_consumed': consumed_nutrition['dietary_fibre_g'],
            'sodium_consumed': consumed_nutrition['sodium_mg'],
            'calcium_consumed': consumed_nutrition['calcium_mg'],
            'added_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        daily_nutrition_df = pd.concat([daily_nutrition_df, pd.DataFrame([new_entry])], ignore_index=True)
        self.csv_handler.write_csv(daily_nutrition_df, self.daily_nutrition_file)

        # Update servings_remaining (subtract consumed servings)
        try:
            self.csv_handler.update_servings_remaining(meal_id, -servings_consumed)
        except Exception as e:
            print(f"Could not update servings_remaining: {e}")

        return new_entry

    def get_daily_nutrition(self, date: str) -> List[Dict]:
        """Get all nutrition entries for a specific date"""
        daily_nutrition_df = self.csv_handler.read_csv(self.daily_nutrition_file)
        if daily_nutrition_df.empty:
            return []

        day_entries = daily_nutrition_df[daily_nutrition_df['date'] == date]
        return day_entries.to_dict('records')

    def remove_daily_nutrition_entry(self, date: str, entry_id: int):
        """Remove a specific entry from daily nutrition"""
        daily_nutrition_df = self.csv_handler.read_csv(self.daily_nutrition_file)
        if daily_nutrition_df.empty:
            return

        # Find the entry to get meal_id and servings_consumed before removing
        entry_mask = (daily_nutrition_df['date'] == date) & (daily_nutrition_df['entry_id'] == entry_id)
        if entry_mask.any():
            entry = daily_nutrition_df[entry_mask].iloc[0]
            meal_id = entry['meal_id']
            servings_consumed = entry['servings_consumed']

            # Remove the entry
            daily_nutrition_df = daily_nutrition_df[~entry_mask]
            self.csv_handler.write_csv(daily_nutrition_df, self.daily_nutrition_file)

            # Add servings back to servings_remaining
            try:
                self.csv_handler.update_servings_remaining(meal_id, servings_consumed)
            except Exception as e:
                print(f"Could not update servings_remaining: {e}")
        else:
            print(f"Entry not found: date={date}, entry_id={entry_id}")

    def clear_daily_nutrition(self, date: str):
        """Clear all nutrition entries for a specific date"""
        daily_nutrition_df = self.csv_handler.read_csv(self.daily_nutrition_file)
        if daily_nutrition_df.empty:
            return

        # Get all entries for the date to restore servings_remaining
        date_entries = daily_nutrition_df[daily_nutrition_df['date'] == date]

        # Restore servings for each entry
        for _, entry in date_entries.iterrows():
            try:
                meal_id = entry['meal_id']
                servings_consumed = entry['servings_consumed']
                self.csv_handler.update_servings_remaining(meal_id, servings_consumed)
            except Exception as e:
                print(f"Could not restore servings for meal {entry['meal_id']}: {e}")

        # Remove all entries for the date
        daily_nutrition_df = daily_nutrition_df[daily_nutrition_df['date'] != date]
        self.csv_handler.write_csv(daily_nutrition_df, self.daily_nutrition_file)

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
            'servings': meal['servings'],
            'ingredients_list': meal['ingredients_list'],
            'quantities_list': meal['quantities_list'],
            # Total nutrition
            'total_calories': meal['total_calories'],
            'total_protein': meal['total_protein'],
            'total_fat_total': meal['total_fat_total'],
            'total_fat_saturated': meal['total_fat_saturated'],
            'total_carbohydrate': meal['total_carbohydrate'],
            'total_sugars': meal['total_sugars'],
            'total_dietary_fibre_g': meal['total_dietary_fibre_g'],
            'total_sodium_mg': meal['total_sodium_mg'],
            'total_calcium_mg': meal['total_calcium_mg'],
            # Per serving nutrition
            'calories_per_serving': meal['calories_per_serving'],
            'protein_per_serving': meal['protein_per_serving'],
            'fat_total_per_serving': meal['fat_total_per_serving'],
            'fat_saturated_per_serving': meal['fat_saturated_per_serving'],
            'carbohydrate_per_serving': meal['carbohydrate_per_serving'],
            'sugars_per_serving': meal['sugars_per_serving'],
            'dietary_fibre_per_serving': meal['dietary_fibre_per_serving'],
            'sodium_per_serving': meal['sodium_per_serving'],
            'calcium_per_serving': meal['calcium_per_serving'],
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

    def _calculate_per_serving_nutrition(self, total_nutrition: Dict, servings: int) -> Dict:
        """Calculate per-serving nutrition from total nutrition"""
        if servings <= 0:
            servings = 1  # Prevent division by zero

        per_serving = {}
        for key, value in total_nutrition.items():
            per_serving[key] = round(value / servings, 2)

        return per_serving

    def _calculate_consumed_nutrition(self, meal: Dict, servings_consumed: float) -> Dict:
        """Calculate nutrition for consumed servings of a meal"""
        consumed_nutrition = {}

        # Per-serving nutrition fields in the meal dict
        per_serving_fields = {
            'calories': 'calories_per_serving',
            'protein': 'protein_per_serving',
            'fat_total': 'fat_total_per_serving',
            'fat_saturated': 'fat_saturated_per_serving',
            'carbohydrate': 'carbohydrate_per_serving',
            'sugars': 'sugars_per_serving',
            'dietary_fibre_g': 'dietary_fibre_per_serving',
            'sodium_mg': 'sodium_per_serving',
            'calcium_mg': 'calcium_per_serving'
        }

        for key, field in per_serving_fields.items():
            per_serving_value = meal.get(field, 0)
            consumed_nutrition[key] = round(per_serving_value * servings_consumed, 2)

        return consumed_nutrition