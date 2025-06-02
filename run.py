import os
import sys

# Activate virtual environment (optional - you can do this manually)
PROJECT_DIR = r"C:\Users\tomco\Documents\Projects\el_plan"
os.chdir(PROJECT_DIR)

# Run the Flask app
if __name__ == '__main__':
    from app import app
    print("Starting Nutrition & Meal Planning App...")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='localhost', port=5000)