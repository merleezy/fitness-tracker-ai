from functools import wraps
from flask import session, flash, redirect, url_for
from random import choice
from sqlalchemy import func
from app.models import Meal, Recommendation, WeightLog
import requests

API_KEY = "hrPOFFDM31cGKPKhl0uHkTs2gBrMIYVc8oHIUaqk"

def analyze_weight_trend(user_id):
    logs = WeightLog.query.filter_by(user_id=user_id).order_by(WeightLog.date.asc()).all()

    if len(logs) < 2:
        return None  # Not enough data

    first = logs[0]
    last = logs[-1]

    delta_days = (last.date - first.date).days
    if delta_days == 0:
        return None  # Avoid division by zero

    delta_weight = last.weight - first.weight
    rate_per_week = (delta_weight / delta_days) * 7

    return {
        "change": round(delta_weight, 1),
        "rate_per_week": round(rate_per_week, 2),
        "since": first.date.strftime("%b %d")
    }

def search_usda_food(query, max_results=5):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": query,
        "pageSize": max_results
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []
    for item in data.get("foods", []):
        food_name = item["description"]
        nutrients = {n['nutrientName']: n['value'] for n in item.get("foodNutrients", [])}
        macros = {
            "name": food_name,
            "calories": nutrients.get("Energy", 0),
            "protein": nutrients.get("Protein", 0),
            "carbs": nutrients.get("Carbohydrate, by difference", 0),
            "fat": nutrients.get("Total lipid (fat)", 0)
        }
        results.append(macros)

    return results

def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to access that page.", "warning")
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped_view

def estimate_tdee(user):
    # Harris-Benedict Formula for BMR
    weight_kg = user.weight * 0.4536
    height_cm = user.height * 2.54
    age = user.age

    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5 

    # Activity multiplier: moderate default
    if user.fitness_goal == 'cutting':
        tdee = bmr * 1.4
    elif user.fitness_goal == 'lean muscle':
        tdee = bmr * 1.6
    elif user.fitness_goal == 'endurance':
        tdee = bmr * 1.7
    else:
        tdee = bmr * 1.5

    return round(tdee)

def average_recent_macros(user_id, limit=3):
    recent_meals = Meal.query.filter_by(user_id=user_id).order_by(Meal.id.desc()).limit(limit).all()
    if not recent_meals:
        return None

    avg = {
        'calories': sum(m.calories for m in recent_meals) / len(recent_meals),
        'protein': sum(m.protein for m in recent_meals) / len(recent_meals),
        'carbs': sum(m.carbs for m in recent_meals) / len(recent_meals),
        'fats': sum(m.fats for m in recent_meals) / len(recent_meals)
    }

    return {k: round(v, 1) for k, v in avg.items()}

def get_user_feedback_stats(user_id):
    """Returns lists of meals/workouts that are frequently followed or skipped."""
    from app.models import Recommendation, db

    # Count how many times each item was followed or skipped
    feedback = db.session.query(
        Recommendation.meal_rec,
        Recommendation.followed,
        func.count().label('count')
    ).filter(
        Recommendation.user_id == user_id,
        Recommendation.followed != None
    ).group_by(Recommendation.meal_rec, Recommendation.followed).all()

    followed_meals = set()
    skipped_meals = set()

    for meal, status, count in feedback:
        if count >= 2:  # Optional threshold to avoid 1-off decisions
            if status == 'followed':
                followed_meals.add(meal)
            elif status == 'skipped':
                skipped_meals.add(meal)

    # Repeat for workouts
    feedback = db.session.query(
        Recommendation.workout_rec,
        Recommendation.followed,
        func.count().label('count')
    ).filter(
        Recommendation.user_id == user_id,
        Recommendation.followed != None
    ).group_by(Recommendation.workout_rec, Recommendation.followed).all()

    followed_workouts = set()
    skipped_workouts = set()

    for workout, status, count in feedback:
        if count >= 2:
            if status == 'followed':
                followed_workouts.add(workout)
            elif status == 'skipped':
                skipped_workouts.add(workout)

    return followed_meals, skipped_meals, followed_workouts, skipped_workouts

def generate_recommendation(user):
    goal = user.fitness_goal

    # --- CUTTING GOAL ---
    cutting_meals = [
        "Grilled Chicken & Steamed Broccoli",
        "Turkey Lettuce Wraps",
        "Egg Whites + Oats",
        "Zucchini Noodles + Lean Ground Turkey",
        "Cauliflower Fried Rice + Shrimp",
        "Tuna Salad with Avocado",
        "Greek Yogurt + Berries",
        "Cottage Cheese + Almonds",
        "Steak Salad with Olive Oil",
        "Boiled Eggs + Spinach"
    ]
    cutting_workouts = [
        "30 min HIIT",
        "45 min Fasted Cardio",
        "Full Body Calisthenics Circuit",
        "Tabata Training",
        "Jump Rope + Bodyweight Mix",
        "Outdoor Run (3 miles)",
        "Weighted Circuit Training",
        "Incline Walking",
        "Kickboxing"
    ]

    # --- LEAN MUSCLE GAIN GOAL ---
    muscle_meals = [
        "Steak + Brown Rice + Veggies",
        "Quinoa + Chicken + Avocado",
        "Salmon + Sweet Potato",
        "Ground Turkey Tacos (Whole Wheat)",
        "Lentil Stew + Grilled Chicken",
        "Greek Yogurt Smoothie + Granola",
        "Tofu + Stir-Fried Vegetables + Rice",
        "Cottage Cheese + Banana + Peanut Butter",
        "High-Protein Pasta Bowl"
    ]
    muscle_workouts = [
        "Push-Pull-Legs Split",
        "Upper/Lower Body Split",
        "Heavy Compound Lifting (Squat/Deadlift)",
        "Chest + Triceps Day",
        "Back + Biceps Routine",
        "Shoulder & Core Superset",
        "Barbell Complexes",
        "Progressive Overload Program"
    ]

    # --- ENDURANCE GOAL ---
    endurance_meals = [
        "Whole Grain Pasta + Turkey Meatballs",
        "Protein Smoothie + Banana",
        "Oatmeal + Chia Seeds + Almond Butter",
        "Sweet Potato Hash + Eggs",
        "Energy Bars + Protein Yogurt",
        "Salmon + Brown Rice + Greens",
        "Bean & Veggie Burrito Bowl",
        "Trail Mix + Greek Yogurt"
    ]
    endurance_workouts = [
        "5K Training Program",
        "Interval Running (Run/Walk)",
        "Cycling (40 min steady-state)",
        "Swimming Laps (30-60 min)",
        "Rowing Machine Intervals",
        "Hiking with Pack (1 hr+)",
        "Stadium Stairs + Core Superset",
        "Boxing + Jump Rope"
    ]

    # --- BALANCED / DEFAULT GOAL ---
    balanced_meals = [
        "Grilled Chicken + Rice Bowl",
        "Shrimp Stir-Fry + Mixed Veggies",
        "Turkey Sandwich + Sweet Potato",
        "Veggie Omelet + Whole Wheat Toast",
        "Tofu Bowl + Edamame + Brown Rice",
        "Salmon + Couscous + Spinach",
        "Whole Wheat Wrap + Turkey + Hummus"
    ]
    balanced_workouts = [
        "30 min Mixed Cardio",
        "Full Body Dumbbell Routine",
        "Pilates or Yoga Flow",
        "Basic Strength Training (3x/week)",
        "Spin Class + Light Core Work",
        "Bodyweight Supersets",
        "Resistance Band Conditioning",
        "Cardio + Stretching Combo"
    ]

    if goal == "cutting":
        meal_opts = cutting_meals[:]
        workout_opts = cutting_workouts[:]
    elif goal == "lean muscle":
        meal_opts = muscle_meals[:]
        workout_opts = muscle_workouts[:]
    elif goal == "endurance":
        meal_opts = endurance_meals[:]
        workout_opts = endurance_workouts[:]
    else:
        meal_opts = balanced_meals[:]
        workout_opts = balanced_workouts[:]

    # === Analyze Weight Trend ===
    trend = analyze_weight_trend(user.id)
    trend_note = ""

    if trend:
        rate = trend["rate_per_week"]
        since = trend["since"]

        if user.fitness_goal == "cutting":
            if abs(rate) < 0.2:
                # Weight is stalling or making very slow progress
                meal_opts += [
                    "Zucchini Noodle Bowl with Turkey Meatballs",
                    "Kale + Grilled Chicken Salad with Olive Oil Vinaigrette",
                    "Cauliflower Rice Stir-Fry with Egg Whites"
                ]
                workout_opts += [
                    "Extra HIIT Session (20-30 min)",
                    "Fast-Paced Full-Body Circuit",
                    "Incline Walk + Core Finisher"
                ]
                trend_note = (
                    f"Your weight hasn't changed much since {since}. "
                    "Try tightening your meal portions or increasing workout intensity."
                )

            elif rate < -2:
                # Weight dropping too quickly (rapid weight loss)
                meal_opts += [
                    "Maintenance Bowl: Salmon, Quinoa, Avocado, Roasted Veggies",
                    "Refeed Meal: Steak, Roasted Sweet Potato, Sautéed Spinach",
                    "Protein-Packed Omelet with Whole Eggs and Toast"
                ]
                workout_opts += [
                    "Mobility Recovery + Light Walk",
                    "Yoga Flow + Deep Stretch",
                    "Zone 2 Cardio (e.g., 45 min bike or walk)"
                ]
                trend_note = (
                    f"You're losing weight too quickly (< -2 lbs/week since {since}). "
                    "Consider a maintenance day or refeed to preserve muscle and energy."
                )

            elif rate > 1:
                # Gaining weight on a cutting goal (should not be happening)
                meal_opts += [
                    "Balanced Bowl with Veggies + Lean Protein",
                    "Healthy Salad with Chicken + Balsamic Dressing",
                    "Grilled Chicken + Zucchini Noodles"
                ]
                workout_opts += [
                    "Strength Training (Full Body)",
                    "Medium-Intensity Cardio (30-40 mins)",
                    "Bodyweight HIIT"
                ]
                trend_note = (
                    f"You're gaining weight despite a cutting goal since {since}. "
                    "Make sure your calorie intake is properly aligned with your goal."
                )

        elif user.fitness_goal == "lean muscle":
            if rate < 0.1:
                # Slow muscle gain (muscle gain progress is stagnating)
                meal_opts += [
                    "Chicken Thighs with Jasmine Rice and Avocado",
                    "High-Calorie Protein Shake with Nut Butter & Oats",
                    "Ground Beef and Potato Bowl with Veggies"
                ]
                workout_opts += [
                    "Heavy Strength Training",
                    "Push-Pull-Legs Split",
                    "Upper/Lower Body Split with Progressive Overload"
                ]
                trend_note = (
                    f"Muscle gain progress has slowed since {since}. "
                    "Add more calories and focus on progressive overload in workouts."
                )

            elif rate >= 0.5:
                # Healthy muscle gain
                meal_opts += [
                    "Protein-Packed Chicken & Rice",
                    "Tuna Salad with Avocado",
                    "High-Protein Smoothie + Nut Butters"
                ]
                workout_opts += [
                    "Strength Training with Progressive Overload",
                    "Legs + Back Day",
                    "Push-Pull Routine"
                ]
                trend_note = (
                    f"You're gaining muscle well since {since}. Keep up with the strength training and nutrition!"
                )

            elif rate > 1:
                # Rapid muscle gain (warning)
                meal_opts += [
                    "Beef + Potato Bowl with Veggies",
                    "Omelet with Eggs and Avocado",
                    "High-Calorie Smoothie with Oats and Peanut Butter"
                ]
                workout_opts += [
                    "Heavy Resistance Training",
                    "Upper Body Hypertrophy Focus",
                    "Lower Body Strength Training"
                ]
                trend_note = (
                    f"You're gaining muscle too rapidly since {since}. Consider adjusting calorie intake for more controlled gains."
                )

        elif user.fitness_goal == "endurance":
            if abs(rate) < 0.1:
                # No change, endurance improvement still slow
                meal_opts += [
                    "Lean Chicken Wrap with Veggies",
                    "Oatmeal with Banana and Almond Butter",
                    "Tuna Salad on Whole Grain Toast"
                ]
                workout_opts += [
                    "Low-Intensity Steady-State Cardio",
                    "Active Recovery (Yoga/Stretching)",
                    "Moderate-Intensity Running or Cycling"
                ]
                trend_note = (
                    f"Your weight is staying stable since {since}. Focus on increasing your endurance performance."
                )

            elif abs(rate) > 1:
                # Significant weight fluctuation in endurance goal
                meal_opts += [
                    "Healthy Chicken Salad with Quinoa",
                    "Roasted Salmon with Sweet Potato",
                    "Greek Yogurt with Berries"
                ]
                workout_opts += [
                    "HIIT or Interval Training",
                    "Strength + Endurance Circuit",
                    "Long-Distance Running or Cycling"
                ]
                trend_note = (
                    f"You're seeing larger weight fluctuations since {since}. This could indicate changes in muscle/fat distribution, which is normal for endurance training."
                )

        elif user.fitness_goal == "balanced":
            if abs(rate) < 0.2:
                # Maintaining current weight, great for a balanced goal
                meal_opts += [
                    "Grilled Chicken & Veggies",
                    "Turkey Sandwich with Avocado",
                    "Spinach Salad with Grilled Chicken"
                ]
                workout_opts += [
                    "Full-Body Strength Workout",
                    "Cardio + Core",
                    "Yoga + Stretching"
                ]
                trend_note = (
                    f"You're maintaining weight well since {since}. Keep it balanced and focus on strength and performance."
                )

            elif rate > 0.2 and rate < 1:
                # Slowly gaining muscle and improving fitness
                meal_opts += [
                    "Lean Beef + Sweet Potato",
                    "Greek Yogurt with Almonds",
                    "High-Protein Smoothie + Nut Butter"
                ]
                workout_opts += [
                    "Strength Training",
                    "Low-Intensity Cardio",
                    "Active Recovery"
                ]
                trend_note = (
                    f"You're gaining a little weight, but it's likely muscle. Stay consistent with your balanced fitness approach."
                )

            elif rate > 1:
                # Gaining weight faster than expected
                meal_opts += [
                    "Grilled Fish + Avocado",
                    "Protein Shake with Oats and Almond Butter",
                    "Chicken Salad with Olive Oil Dressing"
                ]
                workout_opts += [
                    "Progressive Resistance Training",
                    "High-Intensity Interval Training",
                    "Cardio + Core Strengthening"
                ]
                trend_note = (
                    f"You're gaining weight faster than planned since {since}. Consider re-assessing your calorie intake for a more gradual approach."
                )

    # === Filter Out Last 3 Recommendations ===
    recent_recs = Recommendation.query.filter_by(user_id=user.id).order_by(Recommendation.timestamp.desc()).limit(10).all()
    recent_meals = {r.meal_rec for r in recent_recs}
    recent_workouts = {r.workout_rec for r in recent_recs}

    filtered_meals = [m for m in meal_opts if m not in recent_meals]
    filtered_workouts = [w for w in workout_opts if w not in recent_workouts]

    # === Feedback-Aware Filtering ===
    followed_meals, skipped_meals, followed_workouts, skipped_workouts = get_user_feedback_stats(user.id)

    meal_opts = [m for m in meal_opts if m not in skipped_meals]
    workout_opts = [w for w in workout_opts if w not in skipped_workouts]

    if followed_meals:
        meal_opts = list(followed_meals) + meal_opts
    if followed_workouts:
        workout_opts = list(followed_workouts) + workout_opts

    # === Personalization Based on User Macros and TDEE ===
    tdee = estimate_tdee(user)
    macros = average_recent_macros(user.id)

    if macros:
        low_protein_threshold = 20  # grams
        high_calorie_margin = 0.05  # 5% over TDEE considered high for cutting

        # Case 1: Protein intake is critically low
        if macros['protein'] < low_protein_threshold:
            meal_opts += [
                "Protein Smoothie with Whey + Greek Yogurt & Berries",
                "Egg White Omelet with Avocado + Spinach",
                "Chicken + Tofu Stir-Fry with Edamame and Quinoa"
            ]
            trend_note = (
                trend_note or "" + 
                " Protein intake is low — adding high-protein meals to support your goal."
            )

        # Case 2: User is trying to cut but consuming more than TDEE
        if user.fitness_goal == 'cutting' and macros['calories'] > tdee * (1 + high_calorie_margin):
            meal_opts += [
                "Low-Carb Salad with Lean Chicken + Olive Oil",
                "Zucchini Noodles with Grilled Turkey & Pesto",
                "Grilled Cod or Tilapia with Steamed Broccoli & Cauliflower Mash"
            ]
            trend_note = (
                trend_note or "" + 
                " Your average calorie intake is above your estimated needs. "
                "Try lighter, lower-carb meals to stay in a deficit."
            )

    # === Deduplication and Fallbacks ===
    meal_opts = list(dict.fromkeys(meal_opts))
    workout_opts = list(dict.fromkeys(workout_opts))

    if not filtered_meals:
        filtered_meals = meal_opts
    if not filtered_workouts:
        filtered_workouts = workout_opts

    from random import choice
    return choice(filtered_meals), choice(filtered_workouts), trend_note