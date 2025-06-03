let meals = [];
let dailyNutritionEntries = [];
let selectedMeal = null;
let currentDate = '';

// Initialize page when loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Daily Nutrition page loaded');

    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('selectedDate').value = today;
    currentDate = today;
    document.getElementById('displayDate').textContent = today;

    // Load meals and daily nutrition
    loadMeals();
    loadDailyNutrition();
});

async function loadMeals() {
    try {
        console.log('Loading meals...');
        const response = await fetch('/api/meals');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        meals = await response.json();
        console.log(`Loaded ${meals.length} meals`);

        updateMealsDropdown();

    } catch (error) {
        console.error('Error loading meals:', error);
        showMessage('Error loading meals: ' + error.message, 'danger');
    }
}

function updateMealsDropdown() {
    const select = document.getElementById('mealSelect');
    select.innerHTML = '<option value="">Choose a meal...</option>';

    meals.forEach(meal => {
        const option = document.createElement('option');
        option.value = meal.meal_id;

        // Show remaining servings if available
        let displayText = meal.meal_name;
        if (meal.servings_remaining !== null && meal.servings_remaining !== undefined) {
            const remaining = parseFloat(meal.servings_remaining);
            displayText += ` (${remaining} remaining of ${meal.servings})`;

            // Disable option if no servings remaining
            if (remaining <= 0) {
                option.disabled = true;
                displayText += ' - EMPTY';
            }
        } else {
            displayText += ` (${meal.servings} servings)`;
        }

        option.textContent = displayText;
        select.appendChild(option);
    });
}

async function refreshMeals() {
    showMessage('Refreshing meals...', 'info');
    await loadMeals();
    showMessage('Meals refreshed successfully!', 'success');
}

function onMealSelect() {
    const select = document.getElementById('mealSelect');
    const selectedMealId = parseInt(select.value);

    if (!selectedMealId) {
        selectedMeal = null;
        document.getElementById('addMealBtn').disabled = true;
        document.getElementById('mealPreview').style.display = 'none';
        return;
    }

    selectedMeal = meals.find(meal => meal.meal_id === selectedMealId);
    if (selectedMeal) {
        document.getElementById('addMealBtn').disabled = false;
        updateMealPreview();
    }
}

function updateMealPreview() {
    if (!selectedMeal) return;

    document.getElementById('previewMealName').textContent = selectedMeal.meal_name;
    document.getElementById('previewCalories').textContent = selectedMeal.calories_per_serving || 0;
    document.getElementById('previewProtein').textContent = selectedMeal.protein_per_serving || 0;
    document.getElementById('previewFat').textContent = selectedMeal.fat_total_per_serving || 0;
    document.getElementById('previewCarbs').textContent = selectedMeal.carbohydrate_per_serving || 0;
    document.getElementById('previewServings').textContent = selectedMeal.servings || 1;

    // Show remaining servings if available
    const remainingElement = document.getElementById('previewServingsRemaining');
    const remainingContainer = document.getElementById('previewRemaining');

    if (selectedMeal.servings_remaining !== null && selectedMeal.servings_remaining !== undefined) {
        const remaining = parseFloat(selectedMeal.servings_remaining);
        remainingElement.textContent = remaining;

        // Color code based on availability
        if (remaining <= 0) {
            remainingContainer.className = 'text-danger';
            remainingContainer.innerHTML = 'Remaining: <span id="previewServingsRemaining">0 - EMPTY</span>';
        } else if (remaining <= 1) {
            remainingContainer.className = 'text-warning';
            remainingContainer.innerHTML = 'Remaining: <span id="previewServingsRemaining">' + remaining + ' - LOW</span>';
        } else {
            remainingContainer.className = 'text-success';
            remainingContainer.innerHTML = 'Remaining: <span id="previewServingsRemaining">' + remaining + '</span>';
        }
    } else {
        remainingContainer.className = 'text-muted';
        remainingContainer.innerHTML = 'Remaining: <span id="previewServingsRemaining">Not tracked (old meal)</span>';
    }

    document.getElementById('mealPreview').style.display = 'block';
}

async function addMealToDay() {
    if (!selectedMeal) {
        showMessage('Please select a meal first', 'warning');
        return;
    }

    const servings = parseFloat(document.getElementById('servingsInput').value) || 1;

    if (servings <= 0) {
        showMessage('Servings must be greater than 0', 'warning');
        return;
    }

    // Check if enough servings are available (for meals with tracking)
    if (selectedMeal.servings_remaining !== null && selectedMeal.servings_remaining !== undefined) {
        const available = parseFloat(selectedMeal.servings_remaining);
        if (servings > available) {
            showMessage(`Not enough servings available. Requested: ${servings}, Available: ${available}`, 'danger');
            return;
        }
    }

    try {
        const response = await fetch(`/api/daily-nutrition/${currentDate}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                meal_id: selectedMeal.meal_id,
                servings: servings
            })
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(`Added ${servings} serving(s) of "${selectedMeal.meal_name}" to ${currentDate}`, 'success');

            // Reset form
            document.getElementById('mealSelect').value = '';
            document.getElementById('servingsInput').value = '1';
            document.getElementById('addMealBtn').disabled = true;
            document.getElementById('mealPreview').style.display = 'none';
            selectedMeal = null;

            // Reload meals and daily nutrition to show updated remaining servings
            await loadMeals();
            await loadDailyNutrition();

        } else {
            showMessage('Error adding meal: ' + result.error, 'danger');
        }

    } catch (error) {
        showMessage('Error adding meal: ' + error.message, 'danger');
    }
}

async function loadDailyNutrition() {
    try {
        const response = await fetch(`/api/daily-nutrition/${currentDate}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        dailyNutritionEntries = await response.json();
        console.log(`Loaded ${dailyNutritionEntries.length} entries for ${currentDate}`);

        updateDailyNutritionTable();
        updateNutritionGoals();

    } catch (error) {
        console.error('Error loading daily nutrition:', error);
        showMessage('Error loading daily nutrition: ' + error.message, 'danger');
    }
}

function updateDailyNutritionTable() {
    const tbody = document.getElementById('dailyNutritionBody');
    tbody.innerHTML = '';

    let totals = {
        servings: 0,
        calories: 0,
        protein: 0,
        fat_total: 0,
        fat_saturated: 0,
        carbohydrate: 0,
        sugars: 0,
        dietary_fibre: 0,
        sodium: 0,
        calcium: 0
    };

    dailyNutritionEntries.forEach((entry) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${entry.meal_name}</td>
            <td>${entry.servings_consumed}</td>
            <td>${entry.calories_consumed}</td>
            <td>${entry.protein_consumed}</td>
            <td>${entry.fat_total_consumed}</td>
            <td>${entry.fat_saturated_consumed}</td>
            <td>${entry.carbohydrate_consumed}</td>
            <td>${entry.sugars_consumed}</td>
            <td>${entry.dietary_fibre_consumed}</td>
            <td>${entry.sodium_consumed}</td>
            <td>${entry.calcium_consumed}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="removeDailyNutritionEntry(${entry.entry_id})">
                    Remove
                </button>
            </td>
        `;
        tbody.appendChild(row);

        // Add to totals
        totals.servings += parseFloat(entry.servings_consumed) || 0;
        totals.calories += parseFloat(entry.calories_consumed) || 0;
        totals.protein += parseFloat(entry.protein_consumed) || 0;
        totals.fat_total += parseFloat(entry.fat_total_consumed) || 0;
        totals.fat_saturated += parseFloat(entry.fat_saturated_consumed) || 0;
        totals.carbohydrate += parseFloat(entry.carbohydrate_consumed) || 0;
        totals.sugars += parseFloat(entry.sugars_consumed) || 0;
        totals.dietary_fibre += parseFloat(entry.dietary_fibre_consumed) || 0;
        totals.sodium += parseFloat(entry.sodium_consumed) || 0;
        totals.calcium += parseFloat(entry.calcium_consumed) || 0;
    });

    // Update totals row
    document.getElementById('totalServings').textContent = totals.servings.toFixed(1);
    document.getElementById('totalCalories').textContent = totals.calories.toFixed(1);
    document.getElementById('totalProtein').textContent = totals.protein.toFixed(1);
    document.getElementById('totalFat').textContent = totals.fat_total.toFixed(1);
    document.getElementById('totalSatFat').textContent = totals.fat_saturated.toFixed(1);
    document.getElementById('totalCarbs').textContent = totals.carbohydrate.toFixed(1);
    document.getElementById('totalSugars').textContent = totals.sugars.toFixed(1);
    document.getElementById('totalFiber').textContent = totals.dietary_fibre.toFixed(1);
    document.getElementById('totalSodium').textContent = totals.sodium.toFixed(1);
    document.getElementById('totalCalcium').textContent = totals.calcium.toFixed(1);

    return totals;
}

function updateNutritionGoals() {
    const totals = updateDailyNutritionTable();

    // Daily goals (these could be made configurable)
    const goals = {
        calories: 2500,
        protein: 150,
        fat: 65,
        carbs: 250,
        fiber: 25
    };

    // Update progress bars and text
    updateGoalProgress('calorie', totals.calories, goals.calories);
    updateGoalProgress('protein', totals.protein, goals.protein);
    updateGoalProgress('fat', totals.fat_total, goals.fat);
    updateGoalProgress('carb', totals.carbohydrate, goals.carbs);
    updateGoalProgress('fiber', totals.dietary_fibre, goals.fiber);
}

function updateGoalProgress(nutrient, current, goal) {
    const percentage = Math.min((current / goal) * 100, 100);

    document.getElementById(`${nutrient}Progress`).textContent = current.toFixed(1);
    document.getElementById(`${nutrient}Bar`).style.width = `${percentage}%`;

    // Change bar color based on progress
    const bar = document.getElementById(`${nutrient}Bar`);
    if (percentage >= 100) {
        bar.classList.add('bg-success');
        bar.classList.remove('bg-warning', 'bg-danger');
    } else if (percentage >= 75) {
        bar.classList.add('bg-warning');
        bar.classList.remove('bg-success', 'bg-danger');
    } else {
        bar.classList.add('bg-danger');
        bar.classList.remove('bg-success', 'bg-warning');
    }
}

async function removeDailyNutritionEntry(entryId) {
    if (!confirm('Are you sure you want to remove this meal from today?')) {
        return;
    }

    try {
        const response = await fetch(`/api/daily-nutrition/${currentDate}/entry/${entryId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showMessage('Meal removed from daily nutrition', 'info');
            // Reload both meals and daily nutrition to show updated remaining servings
            await loadMeals();
            await loadDailyNutrition();
        } else {
            const result = await response.json();
            showMessage('Error removing meal: ' + result.error, 'danger');
        }

    } catch (error) {
        showMessage('Error removing meal: ' + error.message, 'danger');
    }
}

async function clearDay() {
    if (!confirm(`Are you sure you want to clear ALL meals from ${currentDate}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/daily-nutrition/${currentDate}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showMessage(`Cleared all meals for ${currentDate}`, 'info');
            // Reload both meals and daily nutrition to show updated remaining servings
            await loadMeals();
            await loadDailyNutrition();
        } else {
            const result = await response.json();
            showMessage('Error clearing day: ' + result.error, 'danger');
        }

    } catch (error) {
        showMessage('Error clearing day: ' + error.message, 'danger');
    }
}

async function onDateChange() {
    const newDate = document.getElementById('selectedDate').value;
    if (newDate !== currentDate) {
        currentDate = newDate;
        document.getElementById('displayDate').textContent = newDate;
        await loadDailyNutrition();
    }
}

// Add event listener for date change
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('selectedDate').addEventListener('change', onDateChange);
});

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