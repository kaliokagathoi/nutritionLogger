import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional


class CSVHandler:
    def __init__(self, csv_dir: str, data_dir: str):
        self.csv_dir = csv_dir  # Main folder with ingredients.csv
        self.data_dir = data_dir  # Data folder for generated CSVs

        # File paths
        self.ingredients_file = os.path.join(csv_dir, "ingredients.csv")
        self.meals_file = os.path.join(data_dir, "meals.csv")
        self.meal_log_file = os.path.join(data_dir, "meal_log.csv")

        self._initialize_csv_files()

    def _initialize_csv_files(self):
        """Create meal CSV files if they don't exist (ingredients.csv already exists)"""

        # Meals database - stores created meal recipes (UPDATED with servings and servings_remaining)
        if not os.path.exists(self.meals_file):
            meals_df = pd.DataFrame(columns=[
                'meal_id', 'meal_name', 'servings', 'servings_remaining', 'ingredients_list', 'quantities_list',
                # Total nutrition
                'total_calories', 'total_protein', 'total_fat_total', 'total_fat_saturated',
                'total_carbohydrate', 'total_sugars', 'total_dietary_fibre_g',
                'total_sodium_mg', 'total_calcium_mg',
                # Per serving nutrition
                'calories_per_serving', 'protein_per_serving', 'fat_total_per_serving',
                'fat_saturated_per_serving', 'carbohydrate_per_serving', 'sugars_per_serving',
                'dietary_fibre_per_serving', 'sodium_per_serving', 'calcium_per_serving',
                'created_date'
            ])
            meals_df.to_csv(self.meals_file, index=False)

        # Meal log - logs when meals are consumed (UPDATED with servings)
        if not os.path.exists(self.meal_log_file):
            meal_log_df = pd.DataFrame(columns=[
                'log_id', 'date', 'meal_time', 'meal_id', 'meal_name', 'servings',
                'ingredients_list', 'quantities_list',
                # Total nutrition
                'total_calories', 'total_protein', 'total_fat_total', 'total_fat_saturated',
                'total_carbohydrate', 'total_sugars', 'total_dietary_fibre_g',
                'total_sodium_mg', 'total_calcium_mg',
                # Per serving nutrition
                'calories_per_serving', 'protein_per_serving', 'fat_total_per_serving',
                'fat_saturated_per_serving', 'carbohydrate_per_serving', 'sugars_per_serving',
                'dietary_fibre_per_serving', 'sodium_per_serving', 'calcium_per_serving',
                'notes'
            ])
            meal_log_df.to_csv(self.meal_log_file, index=False)

    def read_csv(self, file_path: str) -> pd.DataFrame:
        """Safely read CSV file"""
        try:
            return pd.read_csv(file_path)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return pd.DataFrame()

    def write_csv(self, df: pd.DataFrame, file_path: str):
        """Safely write DataFrame to CSV"""
        df.to_csv(file_path, index=False)

    def get_next_id(self, df: pd.DataFrame, id_column: str) -> int:
        """Get next available ID for a dataframe"""
        if df.empty:
            return 1
        return int(df[id_column].max()) + 1

    def ensure_servings_remaining_column(self):
        """Add servings_remaining column to existing meals.csv if it doesn't exist"""
        try:
            meals_df = self.read_csv(self.meals_file)

            if meals_df.empty:
                print("Meals CSV is empty, nothing to update")
                return meals_df

            if 'servings_remaining' not in meals_df.columns:
                # Add servings_remaining column, set to None for existing meals
                # (we don't want to retrospectively apply this to existing meals)
                meals_df['servings_remaining'] = None
                self.write_csv(meals_df, self.meals_file)
                print("Added servings_remaining column to existing meals.csv")
            else:
                print("servings_remaining column already exists")

            return meals_df

        except Exception as e:
            print(f"Error in ensure_servings_remaining_column: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def update_servings_remaining(self, meal_id: int, servings_change: float):
        """Update servings_remaining for a specific meal (positive = add, negative = subtract)"""
        meals_df = self.read_csv(self.meals_file)

        if meals_df.empty:
            return

        # Ensure servings_remaining column exists
        if 'servings_remaining' not in meals_df.columns:
            meals_df['servings_remaining'] = None

        # Find the meal
        meal_mask = meals_df['meal_id'] == meal_id
        if not meal_mask.any():
            raise ValueError(f"Meal with ID {meal_id} not found")

        # Get current servings_remaining (could be NaN for old meals)
        current_remaining = meals_df.loc[meal_mask, 'servings_remaining'].iloc[0]

        # If it's NaN (old meal), we can't track remaining servings
        if pd.isna(current_remaining):
            print(
                f"Warning: Cannot update servings for meal {meal_id} - no servings_remaining data (created before this feature)")
            return

        # Update servings_remaining
        new_remaining = float(current_remaining) + servings_change

        # Don't let it go negative
        if new_remaining < 0:
            print(f"Warning: Attempted to consume more servings than available for meal {meal_id}")
            new_remaining = 0

        meals_df.loc[meal_mask, 'servings_remaining'] = new_remaining
        self.write_csv(meals_df, self.meals_file)

        print(f"Updated meal {meal_id}: servings_remaining = {new_remaining}")
        return new_remaining