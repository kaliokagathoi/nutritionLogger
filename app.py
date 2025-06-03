from flask import Flask, render_template, request, jsonify
import os
import sys

# Add backend to Python path
PROJECT_DIR = r"C:\Users\tomco\Documents\Projects\el_plan"
sys.path.append(os.path.join(PROJECT_DIR, 'backend'))

from csv_handler import CSVHandler
from ingredient_operations import IngredientOperations
from meal_operations import MealOperations

app = Flask(__name__)

# Configuration
CSV_DIR = PROJECT_DIR  # ingredients.csv is in main folder
DATA_DIR = os.path.join(PROJECT_DIR, "data")  # generated CSVs go here
STATIC_DIR = os.path.join(PROJECT_DIR, "static")
TEMPLATES_DIR = os.path.join(PROJECT_DIR, "templates")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Set template and static folders
app.template_folder = TEMPLATES_DIR
app.static_folder = STATIC_DIR

print(f"Project dir: {PROJECT_DIR}")
print(f"Looking for ingredients.csv at: {os.path.join(CSV_DIR, 'ingredients.csv')}")
print(f"Ingredients file exists: {os.path.exists(os.path.join(CSV_DIR, 'ingredients.csv'))}")

# Initialize operations
csv_handler = CSVHandler(CSV_DIR, DATA_DIR)
ingredient_ops = IngredientOperations(csv_handler)
meal_ops = MealOperations(csv_handler)

# Ensure servings_remaining column exists on startup
csv_handler.ensure_servings_remaining_column()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/daily-nutrition')
def daily_nutrition():
    """Daily nutrition tracking page"""
    return render_template('daily_nutrition.html')


@app.route('/api/ingredients')
def get_ingredients():
    """Get all ingredients for dropdown"""
    try:
        print("API call: /api/ingredients")
        ingredients = ingredient_ops.get_all_ingredients()
        print(f"Found {len(ingredients)} ingredients")
        if len(ingredients) > 0:
            print(f"First ingredient: {ingredients[0]}")
        return jsonify(ingredients)
    except Exception as e:
        print(f"Error in get_ingredients: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ingredient/<name>')
def get_ingredient(name):
    """Get specific ingredient details"""
    try:
        ingredient = ingredient_ops.get_ingredient_by_name(name)
        if ingredient:
            return jsonify(ingredient)
        return jsonify({'error': 'Ingredient not found'}), 404
    except Exception as e:
        print(f"Error in get_ingredient: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate-nutrition', methods=['POST'])
def calculate_nutrition():
    """Calculate nutrition for ingredient and quantity"""
    try:
        data = request.json
        print(f"Calculate nutrition request: {data}")
        nutrition = ingredient_ops.calculate_nutrition(data['name'], data['quantity'])
        return jsonify(nutrition)
    except Exception as e:
        print(f"Error in calculate_nutrition: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/meals', methods=['GET', 'POST'])
def meals():
    try:
        if request.method == 'GET':
            """Get all meals"""
            print("GET /api/meals - fetching all meals")
            meals = meal_ops.get_all_meals()
            print(f"Found {len(meals)} meals")
            return jsonify(meals)

        elif request.method == 'POST':
            """Create new meal - UPDATED to handle servings"""
            data = request.json
            print(f"Create meal request: {data}")

            # Extract required parameters
            meal_name = data.get('meal_name')
            servings = data.get('servings', 1)  # Default to 1 if not provided
            ingredients = data.get('ingredients', [])

            # Validate inputs
            if not meal_name:
                return jsonify({'error': 'meal_name is required'}), 400
            if not ingredients:
                return jsonify({'error': 'ingredients list is required'}), 400
            if servings < 1:
                return jsonify({'error': 'servings must be at least 1'}), 400

            print(f"Creating meal: {meal_name}, servings: {servings}, ingredients: {len(ingredients)}")

            # Create the meal
            meal = meal_ops.create_meal(meal_name, servings, ingredients)
            return jsonify(meal)

    except Exception as e:
        print(f"Error in meals endpoint: {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        return jsonify({'error': str(e)}), 500


@app.route('/api/daily-nutrition/<date>', methods=['GET', 'POST', 'DELETE'])
def daily_nutrition_api(date):
    """API endpoints for daily nutrition tracking"""
    try:
        if request.method == 'GET':
            """Get all meals logged for a specific date"""
            daily_meals = meal_ops.get_daily_nutrition(date)
            return jsonify(daily_meals)

        elif request.method == 'POST':
            """Add a meal to a specific date"""
            data = request.json
            meal_id = data.get('meal_id')
            servings = data.get('servings', 1)

            if not meal_id:
                return jsonify({'error': 'meal_id is required'}), 400

            daily_entry = meal_ops.add_meal_to_daily_nutrition(date, meal_id, servings)
            return jsonify(daily_entry)

        elif request.method == 'DELETE':
            """Clear all meals for a specific date"""
            meal_ops.clear_daily_nutrition(date)
            return jsonify({'message': f'Daily nutrition cleared for {date}'})

    except Exception as e:
        print(f"Error in daily_nutrition_api: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/daily-nutrition/<date>/entry/<int:entry_id>', methods=['DELETE'])
def remove_daily_nutrition_entry(date, entry_id):
    """Remove a specific meal entry from daily nutrition"""
    try:
        meal_ops.remove_daily_nutrition_entry(date, entry_id)
        return jsonify({'message': 'Entry removed successfully'})
    except Exception as e:
        print(f"Error removing daily nutrition entry: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/log-meal', methods=['POST'])
def log_meal():
    """Log a meal consumption"""
    try:
        data = request.json
        log = meal_ops.log_meal(
            data['meal_id'],
            data['meal_time'],
            data.get('date'),
            data.get('notes', '')
        )
        return jsonify(log)
    except Exception as e:
        print(f"Error in log_meal: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Nutrition & Meal Planning App...")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='localhost', port=5000)