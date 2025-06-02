let ingredients = [];
let currentMealIngredients = [];
let currentIngredient = null;

// Load ingredients when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadIngredients();
});

async function loadIngredients() {
    try {
        const response = await fetch('/api/ingredients');
        ingredients = await response.json();

        const select = document.getElementById('ingredientSelect');
        select.innerHTML = '<option value="">Choose an ingredient...</option>';

        ingredients.forEach(ingredient => {
            const option = document.createElement('option');
            option.value = ingredient.name;
            option.textContent = ingredient.name;
            select.appendChild(option);
        });
    } catch (error) {
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
    document.getElementById('summaryCalories').textContent = totals.calories.toFixed(1);
    document.getElementById('summaryProtein').textContent = totals.protein.toFixed(1);
    document.getElementById('summaryFat').textContent = totals.fat_total.toFixed(1);
    document.getElementById('summarySatFat').textContent = totals.fat_saturated.toFixed(1);
    document.getElementById('summaryCarbs').textContent = totals.carbohydrate.toFixed(1);
    document.getElementById('summarySugars').textContent = totals.sugars.toFixed(1);
    document.getElementById('summaryFiber').textContent = totals.dietary_fibre_g.toFixed(1);
    document.getElementById('summarySodium').textContent = totals.sodium_mg.toFixed(1);
    document.getElementById('summaryCalcium').textContent = totals.calcium_mg.toFixed(1);
}

function removeIngredient(index) {
    currentMealIngredients.splice(index, 1);
    updateIngredientsTable();
    document.getElementById('saveMealBtn').disabled = currentMealIngredients.length === 0;
}

function clearMeal() {
    currentMealIngredients = [];
    document.getElementById('mealName').value = '';
    updateIngredientsTable();
    document.getElementById('saveMealBtn').disabled = true;
    showMessage('Meal cleared', 'info');
}

async function saveMeal() {
    const mealName = document.getElementById('mealName').value.trim();

    if (!mealName) {
        showMessage('Please enter a meal name', 'warning');
        return;
    }

    if (currentMealIngredients.length === 0) {
        showMessage('Please add at least one ingredient', 'warning');
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
                ingredients: currentMealIngredients
            })
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(`Meal "${mealName}" saved successfully!`, 'success');
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