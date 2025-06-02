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

        # ONLY add servings_remaining for NEW meals (check if column exists)
        if 'servings_remaining' in meals_df.columns or meals_df.empty:
            new_meal['servings_remaining'] = servings

        meals_df = pd.concat([meals_df, pd.DataFrame([new_meal])], ignore_index=True)
        self.csv_handler.write_csv(meals_df, self.csv_handler.meals_file)

        return new_meal

    def update_servings_remaining(self, meal_id: int, servings_consumed: int) -> bool:
        """Decrease servings_remaining when a meal is logged (only if column exists)"""
        meals_df = self.csv_handler.read_csv(self.csv_handler.meals_file)
        if meals_df.empty:
            return False

        # Only update if servings_remaining column exists
        if 'servings_remaining' not in meals_df.columns:
            print(f"servings_remaining column not found in meals.csv - skipping update")
            return False

        mask = meals_df['meal_id'] == meal_id
        if not mask.any():
            return False

        # Get current servings remaining
        current_remaining = meals_df.loc[mask, 'servings_remaining'].iloc[0]
        new_remaining = max(0, current_remaining - servings_consumed)  # Don't go below 0

        # Update the dataframe
        meals_df.loc[mask, 'servings_remaining'] = new_remaining
        self.csv_handler.write_csv(meals_df, self.csv_handler.meals_file)

        print(f"Updated meal {meal_id}: {current_remaining} -> {new_remaining} servings remaining")
        return True

    def log_meal(self, meal_id: int, meal_time: str, servings_consumed: int = 1, date: str = None,
                 notes: str = "") -> Dict:
        """Log a meal consumption and update servings_remaining if applicable"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # Get meal details
        meal = self.get_meal_by_id(meal_id)
        if not meal:
            raise ValueError(f"Meal with ID {meal_id} not found")

        # Check servings remaining only if the column exists
        if 'servings_remaining' in meal:
            servings_remaining = meal.get('servings_remaining', meal.get('servings', 1))
            if servings_consumed > servings_remaining:
                raise ValueError(f"Cannot consume {servings_consumed} servings. Only {servings_remaining} remaining.")
        else:
            servings_remaining = meal.get('servings', 1)  # Fallback for old meals

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

        # ONLY add servings_remaining to log if column exists in meal_log.csv
        if 'servings_remaining' in meal_log_df.columns or meal_log_df.empty:
            if 'servings_remaining' in meal:
                new_log['servings_remaining'] = servings_remaining - servings_consumed
            else:
                new_log['servings_remaining'] = servings_remaining  # No change for old meals

        # Add to log
        meal_log_df = pd.concat([meal_log_df, pd.DataFrame([new_log])], ignore_index=True)
        self.csv_handler.write_csv(meal_log_df, self.csv_handler.meal_log_file)

        # Update servings remaining in meals table (only if column exists)
        if 'servings_remaining' in meal:
            self.update_servings_remaining(meal_id, servings_consumed)

        return new_log

    def get_all_meals(self) -> List[Dict]:
        """Get all created meals"""
        meals_df = self.csv_handler.read_csv(self.csv_handler.meals_file)
        return meals_df.to_dict('records')

    def get_meals_with_remaining_servings(self) -> List[Dict]:
        """Get only meals that have servings remaining (only if column exists)"""
        meals_df = self.csv_handler.read_csv(self.csv_handler.meals_file)
        if meals_df.empty:
            return []

        # Only filter by servings_remaining if column exists
        if 'servings_remaining' in meals_df.columns:
            remaining_meals = meals_df[meals_df['servings_remaining'] > 0]
        else:
            # For backward compatibility, return all meals if no servings_remaining column
            remaining_meals = meals_df

        return remaining_meals.to_dict('records')

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