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

        # Meals database - stores created meal recipes (UPDATED with servings)
        if not os.path.exists(self.meals_file):
            meals_df = pd.DataFrame(columns=[
                'meal_id', 'meal_name', 'servings', 'ingredients_list', 'quantities_list',
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