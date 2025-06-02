let ingredients = [];
let currentMealIngredients = [];
let currentIngredient = null;

// Load ingredients when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, loading ingredients...');
    loadIngredients();
});

async function loadIngredients() {
    try {
        console.log('Fetching ingredients from /api/ingredients');
        const response = await fetch('/api/ingredients');

        console.log('Response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const responseText = await response.text();
        console.log('Raw response:', responseText);

        // Try to parse as JSON
        ingredients = JSON.parse(responseText);
        console.log('Parsed ingredients:', ingredients);

        const select = document.getElementById('ingredientSelect');
        select.innerHTML = '<option value="">Choose an ingredient...</option>';

        ingredients.forEach(ingredient => {
            const option = document.createElement('option');
            option.value = ingredient.name;
            option.textContent = ingredient.name;
            select.appendChild(option);
        });

        console.log(`Loaded ${ingredients.length} ingredients into dropdown`);

    } catch (error) {
        console.error('Error details:', error);
        showMessage('Error loading ingredients: ' + error.message, 'danger');
    }
}

function onIngredientSelect() {
    const select = document.getElementById('ingredientSelect');
    const selectedName = select.value;

    if (!selectedName) {
        document.getElementById('unitDisplay').textContent = 'Select ingredient first';
        document.getElementById('addIngredientBtn').disabled = true;
        currentIngredient = null;
        return;
    }

    currentIngredient = ingredients.find(ing => ing.name === selectedName);
    if (currentIngredient) {
        document.getElementById('unitDisplay').textContent =
            `${currentIngredient.unit_size} ${currentIngredient.unit_def}`;
        document.getElementById('addIngredientBtn').disabled = false;
    }
}

async function addIngredient() {
    const quantity = parseFloat(document.getElementById('quantityInput').value);

    if (!currentIngredient || !quantity || quantity <= 0) {
        showMessage('Please select an ingredient and enter a valid quantity', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/calculate-nutrition', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: currentIngredient.name,
                quantity: quantity
            })
        });

        const nutrition = await response.json();

        // Add to current meal ingredients
        currentMealIngredients.push(nutrition);

        // Update table
        updateIngredientsTable();

        // Clear inputs
        document.getElementById('quantityInput').value = '';
        document.getElementById('ingredientSelect').value = '';
        document.getElementById('unitDisplay').textContent = 'Select ingredient first';
        document.getElementById('addIngredientBtn').disabled = true;
        currentIngredient = null;

        // Update save button
        document.getElementById('saveMealBtn').disabled = currentMealIngredients.length === 0;

    } catch (error) {
        showMessage('Error calculating nutrition: ' + error.message, 'danger');
    }
}

function updateIngredientsTable() {
    const tbody = document.getElementById('ingredientsTableBody');
    tbody.innerHTML = '';

    let totals = {
        calories: 0, protein: 0, fat_total: 0, carbohydrate: 0, dietary_fibre_g: 0,
        fat_saturated: 0, sugars: 0, sodium_mg: 0, calcium_mg: 0
    };

    currentMealIngredients.forEach((ingredient, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${ingredient.name}</td>
            <td>${ingredient.quantity} ${ingredient.unit_def}</td>
            <td>${ingredient.calories}</td>
            <td>${ingredient.protein}</td>
            <td>${ingredient.fat_total}</td>
            <td>${ingredient.carbohydrate}</td>
            <td>${ingredient.dietary_fibre_g}</td>
            <td>
                <button class="btn btn-danger btn-sm btn-remove" onclick="removeIngredient(${index})">
                    Remove
                </button>
            </td>
        `;
        tbody.appendChild(row);

        // Add to totals
        totals.calories += ingredient.calories;
        totals.protein += ingredient.protein;
        totals.fat_total += ingredient.fat_total;
        totals.carbohydrate += ingredient.carbohydrate;
        totals.dietary_fibre_g += ingredient.dietary_fibre_g;
        totals.fat_saturated += ingredient.fat_saturated;
        totals.sugars += ingredient.sugars;
        totals.sodium_mg += ingredient.sodium_mg;
        totals.calcium_mg += ingredient.calcium_mg;
    });

    // Update totals row
    document.getElementById('totalCalories').textContent = totals.calories.toFixed(1);
    document.getElementById('totalProtein').textContent = totals.protein.toFixed(1);
    document.getElementById('totalFat').textContent = totals.fat_total.toFixed(1);
    document.getElementById('totalCarbs').textContent = totals.carbohydrate.toFixed(1);
    document.getElementById('totalFiber').textContent = totals.dietary_fibre_g.toFixed(1);

    // Update nutrition summary
    updateNutritionSummary(totals);
}

function updateNutritionSummary(totals) {
    // Update total nutrition
    document.getElementById('summaryCalories').textContent = totals.calories.toFixed(1);
    document.getElementById('summaryProtein').textContent = totals.protein.toFixed(1);
    document.getElementById('summaryFat').textContent = totals.fat_total.toFixed(1);
    document.getElementById('summarySatFat').textContent = totals.fat_saturated.toFixed(1);
    document.getElementById('summaryCarbs').textContent = totals.carbohydrate.toFixed(1);
    document.getElementById('summarySugars').textContent = totals.sugars.toFixed(1);
    document.getElementById('summaryFiber').textContent = totals.dietary_fibre_g.toFixed(1);
    document.getElementById('summarySodium').textContent = totals.sodium_mg.toFixed(1);
    document.getElementById('summaryCalcium').textContent = totals.calcium_mg.toFixed(1);

    // Update per-serving nutrition
    updatePerServingNutrition(totals);
}

function updatePerServingNutrition(totals = null) {
    const servings = parseInt(document.getElementById('servings').value) || 1;
    document.getElementById('servingCount').textContent = servings;

    // If no totals provided, calculate from current values
    if (!totals) {
        totals = {
            calories: parseFloat(document.getElementById('summaryCalories').textContent) || 0,
            protein: parseFloat(document.getElementById('summaryProtein').textContent) || 0,
            fat_total: parseFloat(document.getElementById('summaryFat').textContent) || 0,
            fat_saturated: parseFloat(document.getElementById('summarySatFat').textContent) || 0,
            carbohydrate: parseFloat(document.getElementById('summaryCarbs').textContent) || 0,
            sugars: parseFloat(document.getElementById('summarySugars').textContent) || 0,
            dietary_fibre_g: parseFloat(document.getElementById('summaryFiber').textContent) || 0,
            sodium_mg: parseFloat(document.getElementById('summarySodium').textContent) || 0,
            calcium_mg: parseFloat(document.getElementById('summaryCalcium').textContent) || 0
        };
    }

    // Calculate per-serving values
    document.getElementById('servingCalories').textContent = (totals.calories / servings).toFixed(1);
    document.getElementById('servingProtein').textContent = (totals.protein / servings).toFixed(1);
    document.getElementById('servingFat').textContent = (totals.fat_total / servings).toFixed(1);
    document.getElementById('servingSatFat').textContent = (totals.fat_saturated / servings).toFixed(1);
    document.getElementById('servingCarbs').textContent = (totals.carbohydrate / servings).toFixed(1);
    document.getElementById('servingSugars').textContent = (totals.sugars / servings).toFixed(1);
    document.getElementById('servingFiber').textContent = (totals.dietary_fibre_g / servings).toFixed(1);
    document.getElementById('servingSodium').textContent = (totals.sodium_mg / servings).toFixed(1);
    document.getElementById('servingCalcium').textContent = (totals.calcium_mg / servings).toFixed(1);
}

function removeIngredient(index) {
    currentMealIngredients.splice(index, 1);
    updateIngredientsTable();
    document.getElementById('saveMealBtn').disabled = currentMealIngredients.length === 0;
}

function clearMeal() {
    currentMealIngredients = [];
    document.getElementById('mealName').value = '';
    document.getElementById('servings').value = '1';
    updateIngredientsTable();
    document.getElementById('saveMealBtn').disabled = true;
    showMessage('Meal cleared', 'info');
}

async function saveMeal() {
    const mealName = document.getElementById('mealName').value.trim();
    const servings = parseInt(document.getElementById('servings').value) || 1;

    if (!mealName) {
        showMessage('Please enter a meal name', 'warning');
        return;
    }

    if (currentMealIngredients.length === 0) {
        showMessage('Please add at least one ingredient', 'warning');
        return;
    }

    if (servings < 1) {
        showMessage('Servings must be at least 1', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/meals', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                meal_name: mealName,
                servings: servings,
                ingredients: currentMealIngredients
            })
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(`Meal "${mealName}" saved successfully with ${servings} serving(s)!`, 'success');
            clearMeal();
        } else {
            showMessage('Error saving meal: ' + result.error, 'danger');
        }

    } catch (error) {
        showMessage('Error saving meal: ' + error.message, 'danger');
    }
}

function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    messageArea.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = messageArea.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}